import { useState, useEffect } from "react";
import { apiGet, apiPost, LOGIN_URL } from "./api";
import Dashboard from "./pages/Dashboard";

const GITHUB_URL = "https://github.com/RAVADA-LAKSHITHA/email-intelligence-assistant";

const FEATURES = [
  "Sorts every email into a category",
  "Finds tasks and deadlines for you",
  "Drafts replies you can edit",
];

const TITLE_STYLE =
  "bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text font-bold text-transparent";

function App() {
  const [user, setUser] = useState(null); // null means "not logged in"
  const [checking, setChecking] = useState(true); // true while we ask the server who we are

  useEffect(() => {
    localStorage.removeItem("userEmail"); // the old login method, no longer used
    apiGet("/api/auth/me")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setChecking(false));
  }, []);

  useEffect(() => {
    const handleExpired = () => setUser(null);
    window.addEventListener("session-expired", handleExpired);
    return () => window.removeEventListener("session-expired", handleExpired);
  }, []);

  async function handleLogout() {
    try {
      await apiPost("/api/auth/logout");
    } catch {
      // even if the server can't be reached, show the logged-out screen
    }
    setUser(null);
  }

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-500">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="glass w-full max-w-lg p-10 text-center">
          <h1 className={`text-4xl ${TITLE_STYLE}`}>AI Email Assistant</h1>
          <p className="mt-3 text-slate-600">
            Connect your Gmail and let AI sort, summarize, and pull out your tasks.
          </p>
          <ul className="mt-6 space-y-2 text-sm text-slate-600">
            {FEATURES.map((feature) => (
              <li key={feature}>✓ {feature}</li>
            ))}
          </ul>
          <a href={LOGIN_URL} className="btn-primary mt-8 inline-block px-8 py-3">
            Connect Gmail
          </a>
          <p className="mt-6 text-xs text-slate-500">
            Private beta: Google only lets approved accounts sign in.{" "}
            <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="underline">
              View the code on GitHub
            </a>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="sticky top-0 z-20 px-3 pt-3">
        <header className="glass mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <h1 className={`text-xl ${TITLE_STYLE}`}>AI Email Assistant</h1>
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-slate-600 sm:inline">{user.email}</span>
            <button onClick={handleLogout} className="btn-ghost text-sm">
              Log out
            </button>
          </div>
        </header>
      </div>
      <main className="mx-auto max-w-6xl p-4 sm:p-6">
        <Dashboard userEmail={user.email} />
      </main>
    </div>
  );
}

export default App;