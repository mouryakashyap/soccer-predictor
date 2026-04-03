import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Parlays from "./pages/Parlays";

type Page = "dashboard" | "parlays";

const PAGE_LABELS: Record<Page, string> = {
  dashboard: "Fixtures",
  parlays: "Parlays",
};

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-0 flex items-stretch justify-between h-14">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-indigo-600 tracking-tight">SoccerEdge</span>
            <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded font-medium">BETA</span>
          </div>

          {/* Page tabs — underline style for clearer active indication */}
          <div className="flex gap-1 items-stretch">
            {(["dashboard", "parlays"] as Page[]).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`relative px-4 text-sm font-medium transition-colors border-b-2 ${
                  page === p
                    ? "text-indigo-600 border-indigo-600"
                    : "text-gray-500 border-transparent hover:text-gray-800 hover:border-gray-300"
                }`}
              >
                {PAGE_LABELS[p]}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-6 py-8">
        {page === "dashboard" ? <Dashboard /> : <Parlays />}
      </main>
    </div>
  );
}
