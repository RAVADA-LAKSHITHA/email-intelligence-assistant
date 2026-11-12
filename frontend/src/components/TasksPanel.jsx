import { useState, useEffect } from "react";
import { apiGet } from "../api";
import { formatDeadline } from "../utils";

function TasksPanel({ userEmail, refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiGet("/api/tasks")
      .then(setData)
      .catch((err) => setError(err.message));
  }, [userEmail, refreshKey]);

  return (
    <section className="glass p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold text-slate-900">Tasks{data ? ` (${data.count})` : ""}</h2>
        {data && data.overdue_count > 0 && (
          <span className="rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-medium text-rose-700">
            {data.overdue_count} overdue
          </span>
        )}
      </div>

      {error && <p className="text-sm text-rose-600">Could not load tasks: {error}</p>}
      {!error && !data && <p className="text-sm text-slate-500">Loading...</p>}
      {data && data.tasks.length === 0 && <p className="text-sm text-slate-500">No tasks. Nice!</p>}

      <ul className="max-h-[55vh] space-y-3 overflow-y-auto pr-1">
        {data &&
          data.tasks.map((task) => (
            <li key={task.email_id} className="border-l-2 border-indigo-200 pl-3">
              <p className="text-sm font-medium text-slate-900">{task.task}</p>
              <p className="truncate text-xs text-slate-500">{task.subject}</p>
              <p className={"mt-1 text-xs " + (task.overdue ? "font-medium text-rose-600" : "text-slate-500")}>
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