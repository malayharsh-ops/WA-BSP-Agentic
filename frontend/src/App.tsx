import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "./pages/Dashboard";
import Queue from "./pages/Queue";
import Campaigns from "./pages/Campaigns";

const qc = new QueryClient();

const NAV = [
  { to: "/", label: "Dashboard" },
  { to: "/queue", label: "Queue" },
  { to: "/campaigns", label: "Campaigns" },
];

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 flex">
          {/* Sidebar */}
          <aside className="w-56 bg-white border-r flex flex-col py-6 px-4 shrink-0">
            <div className="mb-8">
              <span className="text-lg font-bold text-indigo-700">JSW ONE</span>
              <span className="ml-1 text-xs text-gray-400">MSME</span>
            </div>
            <nav className="space-y-1">
              {NAV.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) =>
                    `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-indigo-50 text-indigo-700"
                        : "text-gray-600 hover:bg-gray-50"
                    }`
                  }
                >
                  {label}
                </NavLink>
              ))}
            </nav>
            <div className="mt-auto text-xs text-gray-400 text-center">
              Priya v1.0
            </div>
          </aside>

          {/* Main */}
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/queue" element={<Queue />} />
              <Route path="/campaigns" element={<Campaigns />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
