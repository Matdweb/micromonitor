import React from "react";
import { FaServer } from "react-icons/fa";

export default function Topbar() {
  return (
    <header className="h-14 flex items-center px-6 bg-card-bg border-b border-[#123148]">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded bg-[#071527]">
          <FaServer className="text-accent" />
        </div>
        <h1 className="text-xl font-semibold text-text-primary">MicroMonitor</h1>
      </div>

      <div className="ml-auto flex items-center gap-4">
        <select className="bg-[#071527] text-text-primary px-3 py-1 rounded border border-[#123148]">
          <option>AWS</option>
          <option>Azure</option>
          <option>GCP</option>
        </select>
        <div className="text-text-secondary text-sm">mat-dweb</div>
      </div>
    </header>
  );
}
