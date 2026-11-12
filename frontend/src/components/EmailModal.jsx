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

const SECTION_TITLE = "text-xs font-semibold uppercase tracking-wide text-slate-500";

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
    apiGet(`/api/emails/${emailId}`)
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
      const data = await apiPost(`/api/emails/${emailId}/draft-reply`, { tone });
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 p-4 backdrop-blur-sm"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="glass-strong fade-up max-h-[85vh] w-full max-w-2xl overflow-y-auto p-6"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold text-slate-900">
            {detail ? detail.subject : "Loading..."}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg px-2 text-slate-500 hover:bg-white/80 hover:text-slate-900"
          >
            ✕
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-rose-600">Could not load this email: {error}</p>}

        {detail && (
          <div className="mt-2">
            <p className="text-sm text-slate-600">{detail.sender}</p>
            <p className="text-xs text-slate-500">{formatReceived(detail.received_at)}</p>

            <div className="mt-3 flex flex-wrap gap-2">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeStyle}`}>
                {detail.category || "Uncategorized"}
              </span>
              {detail.has_action_item && (
                <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
                  Action needed
                </span>
              )}
              {deadline && (
                <span className="rounded-full border border-white/80 bg-white/70 px-2.5 py-0.5 text-xs text-slate-600">
                  Due {deadline}
                </span>
              )}
            </div>

            <h3 className={`mt-5 ${SECTION_TITLE}`}>AI summary</h3>
            <p className="mt-1 text-sm text-slate-800">{detail.summary}</p>

            {detail.action_item_description && (
              <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                  What to do
                </p>
                <p className="mt-1 text-sm text-amber-900">{detail.action_item_description}</p>
              </div>
            )}

            {canDraft && (
              <div className="mt-5">
                <h3 className={SECTION_TITLE}>Reply with AI</h3>
                <div className="mt-2 flex gap-2">
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    className="rounded-xl border border-white/80 bg-white/70 px-3 py-1.5 text-sm text-slate-700"
                  >
                    {TONES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                  <button onClick={handleDraft} disabled={drafting} className="btn-primary text-sm">
                    {drafting ? "Writing..." : draft ? "Write again" : "Draft reply"}
                  </button>
                </div>

                {draftError && <p className="mt-2 text-sm text-rose-600">{draftError}</p>}

                {draft && (
                  <div className="mt-3">
                    <textarea
                      value={draft}
                      onChange={(e) => {
                        setDraft(e.target.value);
                        setCopied(false);
                      }}
                      rows={8}
                      className="w-full rounded-xl border border-white/80 bg-white/70 p-3 text-sm text-slate-800"
                    />
                    <div className="mt-2 flex items-center justify-between gap-3">
                      <p className="text-xs text-slate-500">
                        Review and edit before you send. Nothing is sent automatically.
                      </p>
                      <button onClick={handleCopy} className="btn-ghost text-sm">
                        {copied ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            <h3 className={`mt-5 ${SECTION_TITLE}`}>Full message</h3>
            <pre className="mt-1 whitespace-pre-wrap break-words rounded-xl border border-white/80 bg-white/60 p-3 text-sm text-slate-700">
              {bodyText}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default EmailModal;