import { fileUrl } from "../api/videoApi";
import { formatEta, formatSpeed } from "../utils/format";

const LABELS = {
  queued: "Waiting for a free slot…",
  downloading: "Downloading",
  processing: "Combining video and audio…",
  completed: "Done. Your file should be saving now.",
  failed: "The download did not finish",
};

export default function ProgressCard({ job, onReset }) {
  const percent = Math.round((job.progress ?? 0) * 100);
  const working = ["queued", "downloading", "processing"].includes(job.status);
  const meta = [formatSpeed(job.speed_bytes_per_sec), formatEta(job.eta_seconds)].filter(Boolean).join(" · ");

  return (
    <section aria-live="polite" className="mt-8 rounded-md border border-line bg-card p-5">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-lg font-bold">{LABELS[job.status]}</h2>
        {job.status === "downloading" && <span className="text-lg font-bold tabular-nums">{percent}%</span>}
      </div>
      {job.title && <p className="mt-1 truncate text-sm text-ink-soft">{job.title}</p>}

      {working && (
        <div
          className="mt-4 h-2 overflow-hidden rounded-full bg-paper"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percent}
        >
          <div
            className={`h-2 rounded-full bg-signal transition-[width] duration-500 ${
              job.status === "processing" ? "animate-pulse" : ""
            }`}
            style={{ width: job.status === "processing" ? "100%" : `${Math.max(percent, 2)}%` }}
          />
        </div>
      )}
      {meta && job.status === "downloading" && <p className="mt-2 text-sm text-ink-soft">{meta}</p>}

      {job.status === "failed" && (
        <p role="alert" className="mt-3 text-sm text-danger">
          {job.error}
        </p>
      )}

      <div className="mt-5 flex flex-wrap gap-3">
        {job.status === "completed" && (
          <a
            href={fileUrl(job.id)}
            className="rounded-md bg-signal px-5 py-3 font-semibold text-white hover:bg-signal-dark"
          >
            Save again
          </a>
        )}
        {!working && (
          <button
            type="button"
            onClick={onReset}
            className="rounded-md border border-line px-5 py-3 font-semibold hover:border-ink-faint"
          >
            {job.status === "failed" ? "Try again" : "Download another video"}
          </button>
        )}
      </div>
    </section>
  );
}
