export function formatBytes(bytes) {
  if (!bytes) return "size unknown";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${value.toFixed(value >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
}

export function formatDuration(totalSeconds) {
  if (!totalSeconds) return "";
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = Math.floor(totalSeconds % 60);
  const mm = String(m).padStart(h ? 2 : 1, "0");
  const ss = String(s).padStart(2, "0");
  return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

export const formatSpeed = (bps) => (bps ? `${formatBytes(bps)}/s` : "");

export function formatEta(seconds) {
  if (seconds == null) return "";
  if (seconds < 60) return `${seconds}s left`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s left`;
}
