# Clipdock - YouTube video downloader (React + Tailwind + FastAPI)

Paste a YouTube link, pick a format and resolution, and download the file in the
same quality and roughly the same size as the stream the YouTube player uses.

> Only download content you own, that is in the public domain, or that you have
> permission to save. Downloading may violate YouTube's Terms of Service.

## How the quality matches YouTube

YouTube serves HD video and audio as **separate streams**. The backend downloads the
best video-only and audio-only streams and merges them with **ffmpeg without
re-encoding**, so nothing is lost and the size matches the original.

| Format | Streams | Container | When to use |
|---|---|---|---|
| Best quality | AV1 / VP9 + Opus | MKV | Sharpest picture, smallest file (VLC, mpv, most modern players) |
| Plays everywhere | H.264 + AAC | MP4 | Phones, TVs, editors. Files are larger at the same quality |
| Audio only | Best audio | MP3 | Music, podcasts |

The resolution list is built from the video itself, with an estimated size per row.

## Project structure

```
video-downloader/
├── backend/                  FastAPI service
│   ├── app/
│   │   ├── main.py           app factory, lifespan, CORS, error handler
│   │   ├── exceptions.py     typed errors -> clean JSON responses
│   │   ├── core/             settings (env-driven), logging
│   │   ├── api/
│   │   │   ├── deps.py       dependency injection
│   │   │   └── v1/           versioned routes: health, videos, downloads
│   │   ├── schemas/          Pydantic request/response models
│   │   ├── services/
│   │   │   ├── ytdlp_service.py   yt-dlp wrapper (formats, sizes, progress)
│   │   │   └── job_manager.py     bounded thread pool, job store, cleanup
│   │   └── utils/validators.py    URL allow-list
│   ├── tests/
│   ├── requirements.txt / requirements-dev.txt
│   └── Dockerfile
├── frontend/                 React 18 + Vite + Tailwind 3
│   └── src/
│       ├── api/              fetch client + endpoint functions
│       ├── hooks/            useVideoInfo, useDownload (polling)
│       ├── components/       UrlForm, VideoPreview, QualitySelector, ProgressCard…
│       └── utils/            formatting helpers
├── docker-compose.yml
└── README.md
```

## Run locally

### Prerequisites

- Python 3.10+ and Node.js 18+
- **ffmpeg** on your PATH (required to merge HD streams). Check: `ffmpeg -version`
  - Windows: `winget install ffmpeg` - macOS: `brew install ffmpeg` - Ubuntu: `sudo apt install ffmpeg`
- **Deno** (recommended). Recent yt-dlp versions use a JavaScript runtime to unlock all
  YouTube formats. Without it you may only see low-quality formats.
  Windows: `winget install DenoLand.Deno` - macOS: `brew install deno`

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to the backend.

### Docker (optional)

```bash
docker compose up --build
```

Open http://localhost:8080.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Liveness + whether ffmpeg is installed |
| POST | `/api/v1/videos/info` | `{url}` -> title, thumbnail, qualities with sizes |
| POST | `/api/v1/downloads` | `{url, height, profile}` -> job (202) |
| GET | `/api/v1/downloads/{id}` | Job status, progress, speed, ETA |
| GET | `/api/v1/downloads/{id}/file` | Stream the finished file |
| DELETE | `/api/v1/downloads/{id}` | Remove a finished job and its file |

## Configuration

Environment variables (prefix `YTD_`, see `backend/.env.example`):
`CORS_ORIGINS`, `DOWNLOAD_DIR`, `MAX_CONCURRENT_DOWNLOADS`, `MAX_ACTIVE_JOBS`,
`FILE_TTL_SECONDS`, `MAX_DURATION_SECONDS`, `ENVIRONMENT`, `LOG_LEVEL`.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Scaling notes

What is already production-minded: typed settings, versioned API, dependency injection,
bounded concurrency, queue limit (HTTP 429), URL allow-list, strict job-id validation,
automatic file cleanup, non-root container, docs disabled in production.

The job store is **in-memory**, so run a single backend process. To scale out:

1. Replace `JobManager`'s dict with Redis and its thread pool with a worker queue (arq, Celery or RQ).
2. Put finished files on shared storage (S3/MinIO) and return signed URLs instead of streaming from disk.
3. Add rate limiting (e.g. `slowapi` or at the reverse proxy) and authentication.
4. Add metrics (Prometheus) and structured JSON logs.

## Troubleshooting: "I picked 1080p but it looks poor"

1. **ffmpeg missing** - without it yt-dlp falls back to a single low-quality file. `GET /api/v1/health` shows `"ffmpeg": true/false`.
2. **No JS runtime** - install Deno (see prerequisites) and update yt-dlp: `pip install -U "yt-dlp[default]"`.
3. **Old yt-dlp** - YouTube changes often; update regularly.
4. **Source is low quality** - some uploads are upscaled; nothing can fix that.
5. **Player compatibility** - AV1/VP9 can stutter on old hardware. Use "Plays everywhere" (H.264/MP4) instead.
