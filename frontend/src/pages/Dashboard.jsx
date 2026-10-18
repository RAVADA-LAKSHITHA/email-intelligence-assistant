import { useState, useEffect } from "react";
import { apiGet } from "../api";
import EmailCard from "../components/EmailCard";

function Dashboard({ userEmail }) {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    apiGet("/api/emails", { email: userEmail })
      .then((data) => setEmails(data.emails))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userEmail]);

  if (loading) return <p className="text-slate-400">Loading your emails...</p>;
  if (error) return <p className="text-red-400">Could not load emails: {error}</p>;
  if (emails.length === 0) {
    return <p className="text-slate-400">No emails yet. A Sync button comes in a later step.</p>;
  }

  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold">Your emails ({emails.length})</h2>
      <div className="space-y-3">
        {emails.map((email) => (
          <EmailCard key={email.id} email={email} />
        ))}
      </div>
    </div>
  );
}

export default Dashboard;