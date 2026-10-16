import { useState } from "react";

export default function UrlForm({ onSubmit, loading }) {
  const [url, setUrl] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url.trim()) onSubmit(url.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
      <label htmlFor="video-url" className="sr-only">
        Video link
      </label>
      <input
        id="video-url"
        type="url"
        required
        autoComplete="off"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://www.youtube.com/watch?v=..."
        className="min-w-0 flex-1 rounded-md border border-line bg-card px-4 py-3 text-base placeholder:text-ink-faint"
      />
      <button
        type="submit"
        disabled={loading || !url.trim()}
        className="rounded-md bg-signal px-6 py-3 font-semibold text-white transition-colors hover:bg-signal-dark disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Loading video…" : "Load video"}
      </button>
    </form>
  );
}
