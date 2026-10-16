export default function Header() {
  return (
    <header className="mb-10">
      <p className="font-display text-lg font-bold tracking-tight text-signal">Clipdock</p>
      <h1 className="mt-6 max-w-xl text-4xl font-bold leading-[1.05] tracking-tight sm:text-5xl">
        Paste a link, then choose how sharp you want it.
      </h1>
      <p className="mt-4 max-w-lg text-ink-soft">
        Files are saved from the same video and audio streams the player uses, so the picture
        and the file size match what you see on screen.
      </p>
    </header>
  );
}
