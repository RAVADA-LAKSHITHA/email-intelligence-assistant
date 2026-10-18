import { CATEGORY_STYLES, formatReceived, formatDeadline } from "../utils";

function EmailCard({ email, onOpen }) {
  const badgeStyle = CATEGORY_STYLES[email.category] || CATEGORY_STYLES.Other;
  const deadline = formatDeadline(email.deadline);

  return (
    <div
      onClick={() => onOpen(email.id)}
      className="cursor-pointer rounded-xl border border-slate-800 bg-slate-800/40 p-4 transition hover:border-slate-600 hover:bg-slate-800/70"
    >
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