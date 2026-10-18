import { useState, useEffect } from "react";
import { LOGIN_URL } from "./api";

const STORAGE_KEY = "userEmail";

function App() {
  const [userEmail, setUserEmail] = useState(() => localStorage.getItem(STORAGE_KEY));

  // After Google login, the backend sends us back with ?login=success&email=...
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const emailFromUrl = params.get("email");
    if (params.get("login") === "success" && emailFromUrl) {
      localStorage.setItem(STORAGE_KEY, emailFromUrl);
      setUserEmail(emailFromUrl);
      window.history.replaceState({}, "", window.location.pathname); // clean the URL
    }
  }, []);

  function handleLogout() {
    localStorage.removeItem(STORAGE_KEY);
    setUserEmail(null);
  }

  if (!userEmail) {
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
          <span className="text-sm text-slate-400">{userEmail}</span>
          <button
            onClick={handleLogout}
            className="rounded-md border border-slate-700 px-3 py-1 text-sm text-slate-300 hover:bg-slate-800"
          >
            Log out
          </button>
        </div>
      </header>
      <main className="p-6">
        <p className="text-slate-400">Connected. Your emails will appear here in the next step.</p>
      </main>
    </div>
  );
}

export default App;