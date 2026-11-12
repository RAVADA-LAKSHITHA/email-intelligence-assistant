export const CATEGORY_STYLES = {
  Work: "bg-blue-100 text-blue-700",
  Personal: "bg-purple-100 text-purple-700",
  Finance: "bg-emerald-100 text-emerald-700",
  Promotions: "bg-orange-100 text-orange-700",
  Security: "bg-rose-100 text-rose-700",
  Social: "bg-pink-100 text-pink-700",
  Education: "bg-cyan-100 text-cyan-700",
  Spam: "bg-slate-200 text-slate-700",
  Other: "bg-slate-200 text-slate-700",
};

// The backend stores times in UTC without a "Z", so we add it before converting to local time.
export function formatReceived(value) {
  if (!value) return "";
  return new Date(value + "Z").toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDeadline(value) {
  if (!value) return null;
  return new Date(value).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}