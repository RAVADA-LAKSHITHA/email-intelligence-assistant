import { useState } from "react";
import { apiGet, apiPost } from "../api";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function progressText(progress) {
  if (!progress || progress.total === 0) return "Checking Gmail...";
  return `Reading emails with AI: ${progress.processed} / ${progress.total}`;
}

function SyncButton({ userEmail, onSynced }) {
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState(null);
  const [message, setMessage] = useState(null);

  async function handleSync() {
    setSyncing(true);
    setProgress(null);
    setMessage(null);

    try {
      // This answers instantly. The real work happens in the background on the server.
      await apiPost("/api/emails/sync", { email: userEmail });

      let lastSaved = 0;
      while (true) {
        await sleep(2000);
        const status = await apiGet("/api/emails/sync/status", { email: userEmail });
        setProgress(status);

        // Show each new email as soon as it is saved.
        if (status.new_saved !== lastSaved) {
          lastSaved = status.new_saved;
          onSynced();
        }

        if (status.status === "done") {
          let text = `${status.new_saved} new email${status.new_saved === 1 ? "" : "s"} added`;
          if (status.failed > 0) text += `, ${status.failed} failed`;
          if (status.stopped_early) text += ". Stopped early because Gemini was busy. Click Sync again.";
          setMessage({ text, isError: status.failed > 0 || status.stopped_early });
          break;
        }
        if (status.status === "error") {
          setMessage({ text: status.error || "Sync failed", isError: true });
          break;
        }
        if (status.status === "idle") {
          setMessage({ text: "Sync stopped (the server restarted). Click Sync again.", isError: true });
          break;
        }
      }
    } catch (err) {
      setMessage({ text: err.message, isError: true });
    } finally {
      setSyncing(false);
      setProgress(null);
    }
  }

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
      <button
        onClick={handleSync}
        disabled={syncing}
        className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
      >
        {syncing ? "Syncing..." : "Sync Gmail"}
      </button>
    </div>
  );
}

export default SyncButton;