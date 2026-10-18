const CATEGORY_STYLES = {
  Work: "bg-blue-500/20 text-blue-300",
  Personal: "bg-purple-500/20 text-purple-300",
  Finance: "bg-green-500/20 text-green-300",
  Promotions: "bg-orange-500/20 text-orange-300",
  Security: "bg-red-500/20 text-red-300",
  Social: "bg-pink-500/20 text-pink-300",
  Education: "bg-cyan-500/20 text-cyan-300",
  Spam: "bg-slate-500/20 text-slate-300",
  Other: "bg-slate-500/20 text-slate-300",
};

// The backend stores times in UTC without a "Z", so we add it before converting to local time.
function formatReceived(value) {
  if (!value) return "";
  return new Date(value + "Z").toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDeadline(value) {
  if (!value) return null;
  return new Date(value).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function EmailCard({ email }) {
  const badgeStyle = CATEGORY_STYLES[email.category] || CATEGORY_STYLES.Other;
  const deadline = formatDeadline(email.deadline);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-800/40 p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="truncate font-semibold text-white">{email.subject}</h3>
          <p className="truncate text-sm text-slate-400">{email.sender}</p>
        </div>
        <span className="shrink-0 text-xs text-slate-500">{formatReceived(email.received_at)}</span>
      </div>

      <p className="mt-3 text-sm text-slate-300">{email.summary}</p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeStyle}`}>
          {email.category || "Uncategorized"}
        </span>
        {email.has_action_item && (
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
    </div>
  );
}

export default EmailCard;