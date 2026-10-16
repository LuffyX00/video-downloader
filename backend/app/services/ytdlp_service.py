"""Thin wrapper around yt-dlp: metadata extraction and downloading.

Quality note: for the "efficient" and "compatible" profiles we download YouTube's
own video-only and audio-only streams and merge them with ffmpeg *without
re-encoding*. The result has the same picture quality and (roughly) the same
size as the stream YouTube would play in the browser.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import yt_dlp
from yt_dlp.utils import YoutubeDLError

from app.core.config import Settings
from app.exceptions import DownloadFailedError, InvalidUrlError, VideoUnavailableError
from app.schemas.download import Profile
from app.schemas.video import QualityOption, VideoInfo

logger = logging.getLogger(__name__)

# Higher is better compression for the same visual quality.
_CODEC_RANK = {"av01": 4, "vp09": 3, "vp9": 3, "hev1": 2, "hvc1": 2, "avc1": 1}
_CODEC_LABEL = {
    "av01": "AV1",
    "vp09": "VP9",
    "vp9": "VP9",
    "hev1": "H.265",
    "hvc1": "H.265",
    "avc1": "H.264",
}

ProgressCallback = Callable[[float, float | None, int | None], None]


# ---------------------------------------------------------------- helpers
def _codec_family(fmt: dict[str, Any]) -> str | None:
    vcodec = fmt.get("vcodec")
    if not vcodec or vcodec == "none":
        return None
    return vcodec.split(".")[0].lower()


def _is_audio_only(fmt: dict[str, Any]) -> bool:
    return fmt.get("vcodec") in (None, "none") and fmt.get("acodec") not in (None, "none")


def _stream_size(fmt: dict[str, Any] | None, duration: int | float | None) -> int | None:
    if not fmt:
        return None
    size = fmt.get("filesize") or fmt.get("filesize_approx")
    if size:
        return int(size)
    tbr = fmt.get("tbr")  # kbit/s -> bytes = tbr * 1000 / 8 * seconds
    if tbr and duration:
        return int(tbr * 125 * duration)
    return None


def _efficiency_key(fmt: dict[str, Any]) -> tuple[int, float]:
    return (_CODEC_RANK.get(_codec_family(fmt) or "", 0), fmt.get("tbr") or 0.0)


def _quality_label(height: int, fps: float | None) -> str:
    return f"{height}p{int(fps)}" if fps and fps > 30 else f"{height}p"


class _ProgressTracker:
    """Turns yt-dlp's per-file hooks into one 0..1 progress value across all streams."""

    def __init__(self, on_progress: ProgressCallback, on_processing: Callable[[], None]):
        self._on_progress = on_progress
        self._on_processing = on_processing
        self._weights: list[float] = [1.0]
        self._order: list[str] = []
        self._fractions: dict[int, float] = {}
        self._finished: set[int] = set()

    def configure(self, formats: list[dict[str, Any]]) -> None:
        sizes = [f.get("filesize") or f.get("filesize_approx") or 0 for f in formats]
        if sizes and all(sizes):
            total = sum(sizes)
            self._weights = [s / total for s in sizes]
        else:
            self._weights = [1 / max(len(formats), 1)] * max(len(formats), 1)

    def hook(self, d: dict[str, Any]) -> None:
        name = d.get("filename") or d.get("tmpfilename") or ""
        if name not in self._order:
            self._order.append(name)
        idx = min(self._order.index(name), len(self._weights) - 1)

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            self._fractions[idx] = min(done / total, 1.0) if total else 0.0
            overall = sum(self._fractions.get(i, 0.0) * w for i, w in enumerate(self._weights))
            eta = d.get("eta")
            self._on_progress(min(overall, 0.99), d.get("speed"), int(eta) if eta else None)
        elif d["status"] == "finished":
            self._fractions[idx] = 1.0
            self._finished.add(idx)
            if len(self._finished) >= len(self._weights):
                self._on_processing()


# ---------------------------------------------------------------- service
class YtDlpService:
    def __init__(self, settings: Settings):
        self._settings = settings

    @staticmethod
    def _base_opts() -> dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 20,
            "retries": 3,
        }

    # -------- metadata
    def extract_info(self, url: str) -> VideoInfo:
        raw = self._fetch(url)
        duration = raw.get("duration")
        formats: list[dict[str, Any]] = raw.get("formats") or []

        audio_streams = [f for f in formats if _is_audio_only(f)]
        best_audio = max(audio_streams, key=lambda f: f.get("abr") or 0, default=None)
        audio_size = _stream_size(best_audio, duration) or 0

        def with_audio(stream: dict[str, Any]) -> int | None:
            size = _stream_size(stream, duration)
            return size + audio_size if size else None

        groups: dict[int, list[dict[str, Any]]] = {}
        for f in formats:
            height = f.get("height")
            if height and f.get("vcodec") not in (None, "none"):
                groups.setdefault(int(height), []).append(f)

        qualities: list[QualityOption] = []
        for height in sorted(groups, reverse=True):
            group = groups[height]
            best = max(group, key=_efficiency_key)
            avc = [f for f in group if _codec_family(f) == "avc1"]
            compat = max(avc, key=lambda f: f.get("tbr") or 0) if avc else best
            family = _codec_family(best)
            qualities.append(
                QualityOption(
                    height=height,
                    label=_quality_label(height, best.get("fps")),
                    fps=int(best["fps"]) if best.get("fps") else None,
                    codec=_CODEC_LABEL.get(family or "", family.upper() if family else None),
                    estimated_size_bytes=with_audio(best),
                    compatible_size_bytes=with_audio(compat),
                )
            )

        if not qualities:
            raise VideoUnavailableError("No downloadable video formats were found.")

        return VideoInfo(
            id=raw.get("id", ""),
            title=raw.get("title") or "Untitled",
            uploader=raw.get("uploader"),
            duration=int(duration) if duration else None,
            thumbnail=raw.get("thumbnail"),
            webpage_url=raw.get("webpage_url") or url,
            audio_size_bytes=audio_size or None,
            qualities=qualities,
        )

    def _fetch(self, url: str) -> dict[str, Any]:
        try:
            with yt_dlp.YoutubeDL(self._base_opts()) as ydl:
                raw = ydl.extract_info(url, download=False)
        except YoutubeDLError as exc:
            logger.warning("yt-dlp metadata extraction failed for %s: %s", url, exc)
            raise VideoUnavailableError() from exc
        self._guard(raw)
        return raw

    def _guard(self, raw: dict[str, Any] | None) -> None:
        if not raw:
            raise VideoUnavailableError()
        if raw.get("_type") == "playlist":
            raise InvalidUrlError("Playlist links are not supported. Paste a single video link.")
        if raw.get("is_live"):
            raise InvalidUrlError("Live streams are not supported.")
        duration = raw.get("duration")
        if duration and duration > self._settings.max_duration_seconds:
            hours = self._settings.max_duration_seconds // 3600
            raise InvalidUrlError(f"Videos longer than {hours} hours are not supported.")

    # -------- download
    @staticmethod
    def _format_opts(height: int | None, profile: Profile) -> dict[str, Any]:
        cap = f"[height<={height}]" if height else ""

        if profile is Profile.audio:
            return {
                "format": "bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}
                ],
            }
        if profile is Profile.compatible:
            return {
                "format": f"bv*{cap}[vcodec^=avc1]+ba[ext=m4a]/bv*{cap}+ba/b{cap}",
                "merge_output_format": "mp4",
            }
        # efficient: yt-dlp's default sort already prefers AV1 > VP9 > H.264 at the same height
        return {"format": f"bv*{cap}+ba/b{cap}", "merge_output_format": "mkv"}

    def download(
        self,
        url: str,
        job_dir: Path,
        height: int | None,
        profile: Profile,
        on_progress: ProgressCallback,
        on_processing: Callable[[], None],
        on_title: Callable[[str], None],
    ) -> Path:
        job_dir.mkdir(parents=True, exist_ok=True)
        tracker = _ProgressTracker(on_progress, on_processing)
        opts = {
            **self._base_opts(),
            **self._format_opts(height, profile),
            "outtmpl": str(job_dir / "%(title).120B [%(id)s].%(ext)s"),
            "windowsfilenames": True,
            "noprogress": True,
            "concurrent_fragment_downloads": 4,
            "retries": 5,
            "fragment_retries": 5,
            "progress_hooks": [tracker.hook],
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self._guard(info)
                on_title(info.get("title") or "Untitled")
                tracker.configure(info.get("requested_formats") or [info])
                result = ydl.process_ie_result(info, download=True)
        except YoutubeDLError as exc:
            logger.warning("yt-dlp download failed for %s: %s", url, exc)
            raise DownloadFailedError() from exc

        return self._locate_output(job_dir, result)

    @staticmethod
    def _locate_output(job_dir: Path, result: dict[str, Any] | None) -> Path:
        downloads = (result or {}).get("requested_downloads") or []
        if downloads and downloads[0].get("filepath"):
            path = Path(downloads[0]["filepath"])
            if path.exists():
                return path
        candidates = [
            p for p in job_dir.iterdir() if p.is_file() and p.suffix not in {".part", ".ytdl"}
        ]
        if not candidates:
            raise DownloadFailedError()
        return max(candidates, key=lambda p: p.stat().st_size)
