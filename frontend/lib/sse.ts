import { useState, useEffect } from "react";
import { Analysis } from "./types";
import { api } from "./api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useAnalysisStream(analysisId: string | null) {
  const [data, setData] = useState<Analysis | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId) return;

    let eventSource: EventSource | null = null;
    let pollInterval: any = null;
    let isTerminated = false;

    // Fetch initial full state
    api
      .getAnalysis(analysisId)
      .then((initial) => {
        setData(initial);
        if (initial.status === "completed" || initial.status === "failed") {
          isTerminated = true;
        }
      })
      .catch((err) => {
        setError(err.message);
      });

    const startPollingFallback = () => {
      if (pollInterval || isTerminated) return;
      pollInterval = setInterval(async () => {
        try {
          const fresh = await api.getAnalysis(analysisId);
          setData(fresh);
          if (fresh.status === "completed" || fresh.status === "failed") {
            clearInterval(pollInterval);
          }
        } catch {
          // ignore polling errors
        }
      }, 2000);
    };

    try {
      eventSource = new EventSource(`${API_BASE}/api/analyses/${analysisId}/stream`);

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      eventSource.addEventListener("snapshot", (e: MessageEvent) => {
        try {
          const snap = JSON.parse(e.data);
          setData((prev) => (prev ? { ...prev, ...snap } : snap));
        } catch {}
      });

      eventSource.addEventListener("progress", (e: MessageEvent) => {
        try {
          const p = JSON.parse(e.data);
          setData((prev) =>
            prev
              ? {
                  ...prev,
                  stage: p.stage,
                  progress: p.progress,
                  ...(p.partial || {}),
                }
              : null
          );
        } catch {}
      });

      eventSource.addEventListener("completed", () => {
        api.getAnalysis(analysisId).then(setData);
        isTerminated = true;
        eventSource?.close();
        setIsConnected(false);
      });

      eventSource.addEventListener("error", () => {
        setIsConnected(false);
        eventSource?.close();
        // Fallback to polling
        startPollingFallback();
      });
    } catch {
      startPollingFallback();
    }

    return () => {
      if (eventSource) eventSource.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [analysisId]);

  return { data, isConnected, error };
}
