import { useState, useEffect } from "react";
import { apiGet } from "../api";
import CategoryTabs from "../components/CategoryTabs";
import EmailCard from "../components/EmailCard";

function Dashboard({ userEmail }) {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState(null);
  const [category, setCategory] = useState(null); // null means "All"
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Tab counts: load once.
  useEffect(() => {
    apiGet("/api/emails/stats", { email: userEmail })
      .then(setStats)
      .catch((err) => setError(err.message));
  }, [userEmail]);

  // Email list: load again whenever the selected tab changes.
  useEffect(() => {
    setLoading(true);
    setError(null);
    apiGet("/api/emails", { email: userEmail, category })
      .then((data) => setEmails(data.emails))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userEmail, category]);

  return (
    <div>
      <CategoryTabs stats={stats} active={category} onChange={setCategory} />

      {error && <p className="text-red-400">Could not load emails: {error}</p>}
      {!error && loading && <p className="text-slate-400">Loading your emails...</p>}
      {!error && !loading && emails.length === 0 && (
        <p className="text-slate-400">No emails here yet.</p>
      )}
      {!error && !loading && emails.length > 0 && (
        <div className="space-y-3">
          {emails.map((email) => (
            <EmailCard key={email.id} email={email} />
          ))}
        </div>
      )}
    </div>
  );
}

export default Dashboard;