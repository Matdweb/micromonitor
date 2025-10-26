import { FaTachometerAlt, FaChartLine, FaServer } from "react-icons/fa";

const ITEMS = [
  { id: "predictions", label: "Predictions", icon: <FaChartLine /> },
  { id: "benchmarks", label: "Benchmarks", icon: <FaTachometerAlt /> },
  { id: "containers", label: "Containers", icon: <FaServer /> },
];

export default function Sidebar({ active, onChange }) {
  return (
    <aside className="w-64 bg-[#071827] border-r border-[#123148] p-4">
      <div className="mb-6 text-text-secondary text-xs uppercase">Sections</div>
      <nav className="space-y-2">
        {ITEMS.map((it) => (
          <button
            key={it.id}
            onClick={() => onChange(it.id)}
            className={
              "w-full flex items-center gap-3 p-3 rounded " +
              (active === it.id
                ? "bg-gradient-to-r from-[#062b38] to-[#083b48] text-accent"
                : "text-text-secondary hover:bg-[#061a20]")
            }
          >
            <span className="text-lg">{it.icon}</span>
            <span className="text-sm">{it.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}