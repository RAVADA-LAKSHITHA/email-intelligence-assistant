import { useState } from "react";
import { apiPost } from "../api";

function SyncButton({ userEmail, onSynced }) {
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState(null);

  async function handleSync() {
    setSyncing(true);
    setMessage(null);
    try {
      const result = await apiPost("/api/emails/sync", { email: userEmail });
      let text = `${result.new_saved} new email${result.new_saved === 1 ? "" : "s"} added`;
      if (result.failed > 0) text += `, ${result.failed} failed (try again in a minute)`;
      setMessage({ text, isError: result.failed > 0 });
      onSynced();
    } catch (err) {
      setMessage({ text: err.message, isError: true });
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      {syncing && <span className="text-xs text-slate-400">Reading new emails with AI...</span>}
      {message && (
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