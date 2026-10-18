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
      const data = await apiGet("/api/emails/digest", { email: userEmail, hours });
      setDigest(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-xl border border-blue-900/50 bg-blue-950/30 p-4">
      <h2 className="font-semibold">AI Digest</h2>
      <p className="mt-1 text-xs text-slate-400">
        One short summary of your recent emails, written by Gemini.
      </p>

      <div className="mt-3 flex gap-2">
        <select
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-200"
        >
          {RANGES.map((r) => (
            <option key={r.hours} value={r.hours}>
              {r.label}
            </option>
          ))}
        </select>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="rounded-md bg-blue-600 px-3 py-1 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {loading ? "Writing..." : "Generate"}
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      {digest && (
        <div className="mt-3">
          <p className="whitespace-pre-line text-sm text-slate-200">{digest.digest}</p>
          <p className="mt-2 text-xs text-slate-500">
            {digest.email_count} emails, {digest.action_count} need action
          </p>
        </div>
      )}
    </section>
  );
}

export default DigestCard;