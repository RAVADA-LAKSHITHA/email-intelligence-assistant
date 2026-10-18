import { useState, useEffect } from "react";
import { apiGet } from "../api";
import CategoryTabs from "../components/CategoryTabs";
import EmailCard from "../components/EmailCard";
import DigestCard from "../components/DigestCard";
import SyncButton from "../components/SyncButton";
import TasksPanel from "../components/TasksPanel";

function Dashboard({ userEmail }) {
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState(null);
  const [category, setCategory] = useState(null); // null means "All"
  const [refreshKey, setRefreshKey] = useState(0); // increase this to reload everything
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiGet("/api/emails/stats", { email: userEmail })
      .then(setStats)
      .catch((err) => setError(err.message));
  }, [userEmail, refreshKey]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiGet("/api/emails", { email: userEmail, category })
      .then((data) => setEmails(data.emails))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userEmail, category, refreshKey]);

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <div className="mb-4 flex justify-end">
          <SyncButton userEmail={userEmail} onSynced={() => setRefreshKey((k) => k + 1)} />
        </div>

        <CategoryTabs stats={stats} active={category} onChange={setCategory} />

        {error && <p className="text-red-400">Could not load emails: {error}</p>}
        {!error && loading && <p className="text-slate-400">Loading your emails...</p>}
        {!error && !loading && emails.length === 0 && (
          <p className="text-slate-400">No emails here yet. Click Sync Gmail.</p>
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
        <TasksPanel userEmail={userEmail} refreshKey={refreshKey} />
      </aside>
    </div>
  );
}

export default Dashboard;