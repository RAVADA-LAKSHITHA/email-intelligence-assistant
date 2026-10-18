import { useState, useEffect } from "react";
import { apiGet } from "../api";
import CategoryTabs from "../components/CategoryTabs";
import EmailCard from "../components/EmailCard";
import DigestCard from "../components/DigestCard";
import TasksPanel from "../components/TasksPanel";

function Dashboard({ userEmail }) {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState(null);
  const [category, setCategory] = useState(null); // null means "All"
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiGet("/api/emails/stats", { email: userEmail })
      .then(setStats)
      .catch((err) => setError(err.message));
  }, [userEmail]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiGet("/api/emails", { email: userEmail, category })
      .then((data) => setEmails(data.emails))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userEmail, category]);

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
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

      <aside className="space-y-4">
        <DigestCard userEmail={userEmail} />
        <TasksPanel userEmail={userEmail} />
      </aside>
    </div>
  );
}

export default Dashboard;