import { useCallback, useRef, useState } from "react";
import { fetchVideoInfo } from "../api/videoApi";

export function useVideoInfo() {
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const requestId = useRef(0);

  const load = useCallback(async (url) => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      const data = await fetchVideoInfo(url);
      if (id === requestId.current) setInfo(data);
    } catch (e) {
      if (id === requestId.current) setError(e.message);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    requestId.current += 1;
    setInfo(null);
    setError(null);
    setLoading(false);
  }, []);

  return { info, loading, error, load, reset };
}
