import { useState } from "react";
import { apiGet } from "../api";

const RANGES = [
  { label: "Last 24 hours", hours: 24 },
  { label: "Last 3 days", hours: 72 },
  { label: "Last 7 days", hours: 168 },
  { label: "Last 30 days", hours: 720 },
];

function DigestCard({ userEmail }) {
  const [hours, setHours] = useState(168);
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet("/api/emails/digest", { hours });
      setDigest(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="glass p-5" data-user={userEmail}>
      <h2 className="font-semibold text-slate-900">AI Digest</h2>
      <p className="mt-1 text-xs text-slate-500">
        One short summary of your recent emails, written by Gemini.
      </p>

      <div className="mt-3 flex gap-2">
        <select
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="rounded-xl border border-white/80 bg-white/70 px-3 py-1.5 text-sm text-slate-700"
        >
          {RANGES.map((r) => (
            <option key={r.hours} value={r.hours}>
              {r.label}
            </option>
          ))}
        </select>
        <button onClick={handleGenerate} disabled={loading} className="btn-primary text-sm">
          {loading ? "Writing..." : "Generate"}
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
      {digest && (
        <div className="mt-4 rounded-xl border border-white/80 bg-white/50 p-3">
          <p className="whitespace-pre-line text-sm text-slate-700">{digest.digest}</p>
          <p className="mt-2 text-xs text-slate-500">
            {digest.email_count} emails, {digest.action_count} need action
          </p>
        </div>
      )}
    </section>
  );
}

export default DigestCard;