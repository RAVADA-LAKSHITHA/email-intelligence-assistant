import { useState, useEffect } from "react";
import { apiGet, apiPost } from "../api";
import { CATEGORY_STYLES, formatReceived, formatDeadline } from "../utils";

// Replying makes no sense for these.
const NO_REPLY_CATEGORIES = ["Promotions", "Spam", "Security", "Social"];

const TONES = [
  { value: "professional", label: "Professional" },
  { value: "friendly", label: "Friendly" },
  { value: "brief", label: "Brief" },
];

function EmailModal({ emailId, userEmail, onClose }) {
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState(null);
  const [tone, setTone] = useState("professional");
  const [draft, setDraft] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [draftError, setDraftError] = useState(null);
  const [copied, setCopied] = useState(false);

  // Load the full email when the window opens.
  useEffect(() => {
    setDetail(null);
    setError(null);
    setDraft("");
    apiGet(`/api/emails/${emailId}`, { email: userEmail })
      .then(setDetail)
      .catch((err) => setError(err.message));
  }, [emailId, userEmail]);

  // Close with the Escape key.
  useEffect(() => {
    function handleKey(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  async function handleDraft() {
    setDrafting(true);
    setDraftError(null);
    setCopied(false);
    try {
      const data = await apiPost(`/api/emails/${emailId}/draft-reply`, {
        email: userEmail,
        tone,
      });
      setDraft(data.draft);
    } catch (err) {
      setDraftError(err.message);
    } finally {
      setDrafting(false);
    }
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(draft);
      setCopied(true);
    } catch {
      setDraftError("Could not copy. Select the text and press Ctrl+C.");
    }
  }

  const badgeStyle = detail ? CATEGORY_STYLES[detail.category] || CATEGORY_STYLES.Other : "";
  const deadline = detail ? formatDeadline(detail.deadline) : null;
  const canDraft = detail && !NO_REPLY_CATEGORIES.includes(detail.category);
  const bodyText = detail
    ? (detail.body && detail.body.trim()) || detail.snippet || "(This email has no text content.)"
    : "";

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-slate-700 bg-slate-900 p-6"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold text-white">
            {detail ? detail.subject : "Loading..."}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-md px-2 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            ✕
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-red-400">Could not load this email: {error}</p>}

        {detail && (
          <div className="mt-2">
            <p className="text-sm text-slate-400">{detail.sender}</p>
            <p className="text-xs text-slate-500">{formatReceived(detail.received_at)}</p>

            <div className="mt-3 flex flex-wrap gap-2">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeStyle}`}>
                {detail.category || "Uncategorized"}
              </span>
              {detail.has_action_item && (
                <span className="rounded-full bg-amber-500/20 px-2.5 py-0.5 text-xs font-medium text-amber-300">
                  Action needed
                </span>
              )}
              {deadline && (
                <span className="rounded-full bg-slate-700 px-2.5 py-0.5 text-xs text-slate-300">
                  Due {deadline}
                </span>
              )}
            </div>

            <h3 className="mt-5 text-xs font-semibold uppercase tracking-wide text-slate-500">
              AI summary
            </h3>
            <p className="mt-1 text-sm text-slate-200">{detail.summary}</p>

            {detail.action_item_description && (
              <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-amber-300">
                  What to do
                </p>
                <p className="mt-1 text-sm text-amber-100">{detail.action_item_description}</p>
              </div>
            )}

            {canDraft && (
              <div className="mt-5">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Reply with AI
                </h3>
                <div className="mt-2 flex gap-2">
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-200"
                  >
                    {TONES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleDraft}
                    disabled={drafting}
                    className="rounded-md bg-blue-600 px-3 py-1 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                  >
                    {drafting ? "Writing..." : draft ? "Write again" : "Draft reply"}
                  </button>
                </div>

                {draftError && <p className="mt-2 text-sm text-red-400">{draftError}</p>}

                {draft && (
                  <div className="mt-3">
                    <textarea
                      value={draft}
                      onChange={(e) => {
                        setDraft(e.target.value);
                        setCopied(false);
                      }}
                      rows={8}
                      className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-slate-200"
                    />
                    <div className="mt-2 flex items-center justify-between gap-3">
                      <p className="text-xs text-slate-500">
                        Review and edit before you send. Nothing is sent automatically.
                      </p>
                      <button
                        onClick={handleCopy}
                        className="rounded-md border border-slate-700 px-3 py-1 text-sm text-slate-300 hover:bg-slate-800"
                      >
                        {copied ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            <h3 className="mt-5 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Full message
            </h3>
            <pre className="mt-1 whitespace-pre-wrap break-words rounded-lg bg-slate-950 p-3 text-sm text-slate-300">
              {bodyText}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default EmailModal;