import { useState, useEffect } from "react";
import { apiGet, apiPost, LOGIN_URL } from "./api";
import Dashboard from "./pages/Dashboard";

function App() {
  const [user, setUser] = useState(null); // null means "not logged in"
  const [checking, setChecking] = useState(true); // true while we ask the server who we are

  // On load: ask the backend who is logged in. The browser sends the cookie by itself.
  useEffect(() => {
    localStorage.removeItem("userEmail"); // the old login method, no longer used
    apiGet("/api/auth/me")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setChecking(false));
  }, []);

  // If the session expires while the app is open, api.js lets us know.
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
      <div className="flex min-h-screen items-center justify-center bg-slate-900">
        <p className="text-slate-400">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <h1 className="text-4xl font-bold text-white">AI Email Intelligence Assistant</h1>
          <p className="mt-3 text-slate-400">
            Connect your Gmail and let AI sort, summarize, and pull out your tasks.
          </p>
          <a
            href={LOGIN_URL}
            className="mt-8 inline-block rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-500"
          >
            Connect Gmail
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
        <h1 className="text-xl font-bold">AI Email Assistant</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-400">{user.email}</span>
          <button
            onClick={handleLogout}
            className="rounded-md border border-slate-700 px-3 py-1 text-sm text-slate-300 hover:bg-slate-800"
          >
            Log out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-6">
        <Dashboard userEmail={user.email} />
      </main>
    </div>
  );
}

export default App;