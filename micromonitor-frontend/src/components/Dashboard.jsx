import React from "react";
import PredictionsPanel from "./panels/PredictionsPanel";
import BenchmarksPanel from "./panels/BenchmarksPanel";
import ContainersPanel from "./panels/ContainersPanel";

export default function Dashboard({ active }) {
  return (
    <div className="space-y-6">
      {active === "predictions" && <PredictionsPanel />}
      {active === "benchmarks" && <BenchmarksPanel />}
      {active === "containers" && <ContainersPanel />}
    </div>
  );
}
