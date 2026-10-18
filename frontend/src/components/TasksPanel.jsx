import { useState, useEffect } from "react";
import { apiGet } from "../api";
import { formatDeadline } from "../utils";


function TasksPanel({ userEmail, refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiGet("/api/tasks", { email: userEmail })
      .then(setData)
      .catch((err) => setError(err.message));
  }, [userEmail, refreshKey]);

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-800/40 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold">Tasks{data ? ` (${data.count})` : ""}</h2>
        {data && data.overdue_count > 0 && (
          <span className="rounded-full bg-red-500/20 px-2.5 py-0.5 text-xs font-medium text-red-300">
            {data.overdue_count} overdue
          </span>
        )}
      </div>

      {error && <p className="text-sm text-red-400">Could not load tasks: {error}</p>}
      {!error && !data && <p className="text-sm text-slate-400">Loading...</p>}
      {data && data.tasks.length === 0 && <p className="text-sm text-slate-400">No tasks. Nice!</p>}

      <ul className="space-y-3">
        {data &&
          data.tasks.map((task) => (
            <li key={task.email_id} className="border-l-2 border-slate-700 pl-3">
              <p className="text-sm text-white">{task.task}</p>
              <p className="truncate text-xs text-slate-500">{task.subject}</p>
              <p className={"mt-1 text-xs " + (task.overdue ? "text-red-400" : "text-slate-400")}>
                {task.deadline
                  ? (task.overdue ? "Overdue: " : "Due ") + formatDeadline(task.deadline)
                  : "No deadline"}
              </p>
            </li>
          ))}
      </ul>
    </section>
  );
}

export default TasksPanel;