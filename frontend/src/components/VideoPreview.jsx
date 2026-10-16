import { formatDuration } from "../utils/format";

export default function VideoPreview({ info }) {
  return (
    <div className="flex gap-4">
      {info.thumbnail && (
        <img
          src={info.thumbnail}
          alt=""
          referrerPolicy="no-referrer"
          className="h-24 w-40 shrink-0 rounded-md bg-line object-cover"
        />
      )}
      <div className="min-w-0">
        <h2 className="line-clamp-2 text-xl font-bold leading-snug">{info.title}</h2>
        <p className="mt-1 text-sm text-ink-soft">
          {[info.uploader, formatDuration(info.duration)].filter(Boolean).join(" · ")}
        </p>
      </div>
    </div>
  );
}
