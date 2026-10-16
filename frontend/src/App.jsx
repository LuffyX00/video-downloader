import { useState } from "react";
import Header from "./components/Header";
import UrlForm from "./components/UrlForm";
import ErrorBanner from "./components/ErrorBanner";
import VideoPreview from "./components/VideoPreview";
import QualitySelector from "./components/QualitySelector";
import ProgressCard from "./components/ProgressCard";
import { useVideoInfo } from "./hooks/useVideoInfo";
import { useDownload } from "./hooks/useDownload";

export default function App() {
  const { info, loading, error: infoError, load, reset: resetInfo } = useVideoInfo();
  const { job, starting, error: downloadError, start, reset: resetDownload } = useDownload();
  const [height, setHeight] = useState(null); // null = highest available
  const [profile, setProfile] = useState("efficient");

  const handleLoad = (url) => {
    resetDownload();
    setHeight(null);
    load(url);
  };

  const handleDownload = () =>
    start({ url: info.webpage_url, height: profile === "audio" ? null : height, profile });

  const handleReset = () => {
    resetDownload();
    resetInfo();
    setHeight(null);
  };

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-5 py-12 sm:py-20">
      <Header />
      <UrlForm onSubmit={handleLoad} loading={loading} />
      <ErrorBanner message={infoError || downloadError} />

      {info && (
        <section className="mt-10 border-t border-line pt-8">
          <VideoPreview info={info} />
          {!job && (
            <QualitySelector
              info={info}
              height={height}
              onHeight={setHeight}
              profile={profile}
              onProfile={setProfile}
              onDownload={handleDownload}
              busy={starting}
            />
          )}
          {job && <ProgressCard job={job} onReset={job.status === "failed" ? resetDownload : handleReset} />}
        </section>
      )}
    </main>
  );
}
