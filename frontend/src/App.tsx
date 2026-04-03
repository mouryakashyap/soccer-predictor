import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Parlays from "./pages/Parlays";

type Page = "dashboard" | "parlays";

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <nav className="bg-white border-b shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-indigo-600">SoccerEdge</span>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">BETA</span>
          </div>
          <div className="flex gap-1">
            {(["dashboard", "parlays"] as Page[]).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                  page === p
                    ? "bg-indigo-600 text-white"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                {p}
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
