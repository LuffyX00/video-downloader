import { formatBytes } from "../utils/format";

const PROFILES = [
  {
    id: "efficient",
    title: "Best quality",
    detail: "AV1 / VP9 with Opus audio, saved as MKV. Smallest file for the sharpest picture.",
  },
  {
    id: "compatible",
    title: "Plays everywhere",
    detail: "H.264 with AAC audio, saved as MP4. Opens on any phone, TV or editor.",
  },
  {
    id: "audio",
    title: "Audio only",
    detail: "Highest-quality sound, saved as MP3.",
  },
];

export const sizeFor = (q, profile, info) => {
  if (profile === "audio") return info.audio_size_bytes;
  return profile === "compatible" ? q.compatible_size_bytes : q.estimated_size_bytes;
};

export default function QualitySelector({ info, height, onHeight, profile, onProfile, onDownload, busy }) {
  const isAudio = profile === "audio";
  const best = info.qualities[0];
  const rows = [
    { ...best, height: null, label: `Highest available (${best.label})` },
    ...info.qualities,
  ];
  const sizes = rows.map((q) => sizeFor(q, profile, info) || 0);
  const maxSize = Math.max(...sizes, 1);
  const selected = rows.find((q) => q.height === height) || rows[0];
  const selectedSize = isAudio ? info.audio_size_bytes : sizeFor(selected, profile, info);

  return (
    <div className="mt-8">
      <fieldset>
        <legend className="mb-3 text-sm font-semibold">Format</legend>
        <div className="grid gap-3 sm:grid-cols-3">
          {PROFILES.map((p) => (
            <label
              key={p.id}
              className={`cursor-pointer rounded-md border p-4 transition-colors ${
                profile === p.id ? "border-signal bg-signal-tint" : "border-line bg-card hover:border-ink-faint"
              }`}
            >
              <input
                type="radio"
                name="profile"
                value={p.id}
                checked={profile === p.id}
                onChange={() => onProfile(p.id)}
                className="sr-only"
              />
              <span className="block font-display font-bold">{p.title}</span>
              <span className="mt-1 block text-sm text-ink-soft">{p.detail}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {!isAudio && (
        <fieldset className="mt-8">
          <legend className="mb-3 text-sm font-semibold">Resolution (bar length shows relative file size)</legend>
          <div className="overflow-hidden rounded-md border border-line bg-card">
            {rows.map((q, i) => {
              const size = sizes[i];
              const active = q.height === height;
              return (
                <label
                  key={q.height ?? "best"}
                  className={`relative flex cursor-pointer items-center gap-4 border-b border-line px-4 py-3 last:border-b-0 ${
                    active ? "bg-signal-tint" : "hover:bg-paper"
                  }`}
                >
                  <input
                    type="radio"
                    name="resolution"
                    checked={active}
                    onChange={() => onHeight(q.height)}
                    className="sr-only"
                  />
                  <span
                    aria-hidden="true"
                    className={`h-3 w-3 shrink-0 rounded-full border-2 ${
                      active ? "border-signal bg-signal" : "border-ink-faint"
                    }`}
                  />
                  <span className="w-44 shrink-0 text-sm font-semibold">
                    {q.label}
                    {q.height !== null && q.codec && profile === "efficient" && (
                      <span className="ml-2 font-normal text-ink-faint">{q.codec}</span>
                    )}
                  </span>
                  <span className="hidden h-2 flex-1 rounded-full bg-paper sm:block">
                    <span
                      className="block h-2 rounded-full bg-amber-bar"
                      style={{ width: `${Math.max((size / maxSize) * 100, 3)}%` }}
                    />
                  </span>
                  <span className="ml-auto w-24 shrink-0 text-right text-sm tabular-nums text-ink-soft">
                    {size ? `~${formatBytes(size)}` : "unknown"}
                  </span>
                </label>
              );
            })}
          </div>
        </fieldset>
      )}

      <button
        type="button"
        onClick={onDownload}
        disabled={busy}
        className="mt-8 w-full rounded-md bg-ink px-6 py-4 text-base font-semibold text-white transition-colors hover:bg-signal-dark disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
      >
        {busy ? "Starting…" : `Download${selectedSize ? ` (about ${formatBytes(selectedSize)})` : ""}`}
      </button>
    </div>
  );
}
