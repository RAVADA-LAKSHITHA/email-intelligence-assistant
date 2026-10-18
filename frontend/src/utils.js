export const CATEGORY_STYLES = {
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