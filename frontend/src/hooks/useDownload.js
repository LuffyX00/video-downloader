import { useCallback, useEffect, useRef, useState } from "react";
import { createDownload, deleteDownload, fileUrl, getDownload } from "../api/videoApi";
import { triggerBrowserDownload } from "../utils/browser";

const POLL_MS = 1000;
const FINAL = ["completed", "failed"];

export function useDownload() {
  const [job, setJob] = useState(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const autoSaved = useRef(null);

  const start = useCallback(async (payload) => {
    setStarting(true);
    setError(null);
    try {
      setJob(await createDownload(payload));
    } catch (e) {
      setError(e.message);
    } finally {
      setStarting(false);
    }
  }, []);

  // Poll until the job reaches a final state.
  useEffect(() => {
    if (!job || FINAL.includes(job.status)) return undefined;
    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const next = await getDownload(job.id);
        if (!cancelled) setJob(next);
      } catch (e) {
        if (cancelled) return;
        if (e.status === 404) {
          setJob((j) => ({ ...j, status: "failed", error: "This download expired. Start it again." }));
        } else {
          setError(e.message);
        }
      }
    }, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [job?.id, job?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  // Save automatically once, the moment the file is ready.
  useEffect(() => {
    if (job?.status === "completed" && autoSaved.current !== job.id) {
      autoSaved.current = job.id;
      triggerBrowserDownload(fileUrl(job.id));
    }
  }, [job]);

  const reset = useCallback(() => {
    if (job && FINAL.includes(job.status)) deleteDownload(job.id).catch(() => {});
    setJob(null);
    setError(null);
  }, [job]);

  return { job, starting, error, start, reset };
}
