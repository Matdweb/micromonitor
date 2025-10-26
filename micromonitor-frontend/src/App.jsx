import React, { useState } from "react";
import Topbar from "./components/Topbar";
import Sidebar from "./components/Sidebar";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [active, setActive] = useState("predictions"); // default tab

  return (
    <div className="min-h-screen flex flex-col">
      <Topbar />
      <div className="flex flex-1">
        <Sidebar active={active} onChange={setActive} />
        <main className="flex-1 p-6 overflow-auto">
          <Dashboard active={active} />
        </main>
      </div>
    </div>
  );
}
