import { useState, useEffect, useRef } from "react";
import { apiGet, apiPost } from "../api";

const AUTO_SYNC_MS = 5 * 60 * 1000; // auto-sync every 5 minutes
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function progressText(progress) {
  if (!progress || progress.total === 0) return "Checking Gmail...";
  return `Reading emails with AI: ${progress.processed} / ${progress.total}`;
}

function SyncButton({ userEmail, onSynced }) {
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState(null);
  const [message, setMessage] = useState(null);
  const [lastSynced, setLastSynced] = useState(null);
  const busy = useRef(false); // true while a sync runs, so two never overlap
  const autoOn = useRef(true); // switched off after an error, so we don't keep retrying

  async function runSync(isAuto) {
    if (busy.current) return;
    busy.current = true;
    setSyncing(true);
    setProgress(null);
    setMessage(null);

    try {
      await apiPost("/api/emails/sync", { email: userEmail });

      let lastSaved = 0;
      while (true) {
        await sleep(2000);
        const status = await apiGet("/api/emails/sync/status", { email: userEmail });
        setProgress(status);

        if (status.new_saved !== lastSaved) {
          lastSaved = status.new_saved;
          onSynced();
        }

        if (status.status === "done") {
          // An automatic sync that found nothing stays quiet.
          const quiet =
            isAuto && status.new_saved === 0 && status.failed === 0 && !status.stopped_early;
          if (!quiet) {
            let text = `${status.new_saved} new email${status.new_saved === 1 ? "" : "s"} added`;
            if (status.failed > 0) text += `, ${status.failed} failed`;
            if (status.stopped_early) text += ". Stopped early because Gemini was busy.";
            setMessage({ text, isError: status.failed > 0 || status.stopped_early });
          }
          setLastSynced(new Date());
          autoOn.current = true;
          break;
        }
        if (status.status === "error") {
          setMessage({ text: status.error || "Sync failed", isError: true });
          autoOn.current = false;
          break;
        }
        if (status.status === "idle") {
          setMessage({ text: "Sync stopped (the server restarted). Click Sync again.", isError: true });
          break;
        }
      }
    } catch (err) {
      setMessage({ text: err.message, isError: true });
      autoOn.current = false;
    } finally {
      busy.current = false;
      setSyncing(false);
      setProgress(null);
    }
  }

  // Sync once when the dashboard opens, then again every few minutes.
  useEffect(() => {
    runSync(true);
    const timer = setInterval(() => {
      if (autoOn.current && !document.hidden) runSync(true);
    }, AUTO_SYNC_MS);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userEmail]);

  return (
    <div className="flex items-center gap-3">
      {syncing && (
        <>
          <span className="text-xs text-slate-400">{progressText(progress)}</span>
          {progress && progress.total > 0 && (
            <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-700">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{ width: `${(progress.processed / progress.total) * 100}%` }}
              />
            </div>
          )}
        </>
      )}
      {!syncing && message && (
        <span className={"text-xs " + (message.isError ? "text-amber-400" : "text-green-400")}>
          {message.text}
        </span>
      )}
      {!syncing && !message && lastSynced && (
        <span className="text-xs text-slate-500">
          Auto-sync on · last checked{" "}
          {lastSynced.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
        </span>
      )}
      <button
        onClick={() => runSync(false)}
        disabled={syncing}
        className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
      >
        {syncing ? "Syncing..." : "Sync Gmail"}
      </button>
    </div>
  );
}

export default SyncButton;