function CategoryTabs({ stats, active, onChange }) {
  if (!stats) return null;

  const categories = Object.entries(stats.by_category)
    .filter(([name]) => name !== "Uncategorized")
    .sort((a, b) => b[1] - a[1]); // biggest category first

  const tabs = [
    { name: null, label: "All", count: stats.total },
    ...categories.map(([name, count]) => ({ name, label: name, count })),
  ];

  return (
    <div className="mb-4 flex flex-wrap gap-2">
      {tabs.map((tab) => {
        const isActive = tab.name === active;
        return (
          <button
            key={tab.label}
            onClick={() => onChange(tab.name)}
            className={
              "rounded-full px-4 py-1.5 text-sm font-medium transition " +
              (isActive
                ? "bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-md shadow-indigo-300/50"
                : "border border-white/80 bg-white/60 text-slate-700 hover:bg-white/90")
            }
          >
            {tab.label} <span className="ml-1 opacity-70">{tab.count}</span>
          </button>
        );
      })}
    </div>
  );
}

export default CategoryTabs;