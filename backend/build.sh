#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

mkdir -p bin

if [ ! -f bin/ffmpeg ]; then
  echo "Downloading ffmpeg..."
  curl -fsSL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o /tmp/ffmpeg.tar.xz
  python - <<'PY'
import os, stat, tarfile
with tarfile.open("/tmp/ffmpeg.tar.xz", "r:xz") as tar:
    for m in tar.getmembers():
        name = os.path.basename(m.name)
        if m.isfile() and name in ("ffmpeg", "ffprobe"):
            m.name = name
            tar.extract(m, "bin")
            os.chmod(f"bin/{name}", os.stat(f"bin/{name}").st_mode | stat.S_IEXEC)
PY
fi

if [ ! -f bin/deno ]; then
  echo "Downloading deno..."
  curl -fsSL https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip -o /tmp/deno.zip
  python - <<'PY'
import os, stat, zipfile
with zipfile.ZipFile("/tmp/deno.zip") as z:
    z.extract("deno", "bin")
os.chmod("bin/deno", os.stat("bin/deno").st_mode | stat.S_IEXEC)
PY
fi

echo "Build finished"