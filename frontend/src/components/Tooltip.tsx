// frontend/src/components/Tooltip.tsx

import React from "react";
import type { TooltipData } from "../types/geojson";

interface TooltipProps {
  data: TooltipData | null;
  x: number;
  y: number;
}

const Tooltip: React.FC<TooltipProps> = ({ data, x, y }) => {
  if (!data) return null;

  const topCbText = data.top_cb_fl > 0 ? `FL${data.top_cb_fl}` : "Pas de nuage convectif";

  return (
    <div
      className="tooltip"
      style={{
        left: x + 10,
        top: y + 10,
      }}
    >
      <h5>Échéance H+{data.echeance_h}</h5>
      <ul>
        <li>CAPE : {data.cape_ml_jkg ?? "N/A"} J/kg</li>
        <li>Précipitations : {data.precip_mm_h ?? "N/A"} mm/h</li>
        <li>Score : {data.score ?? "N/A"}</li>
        <li>Risque : {data.risque}</li>
        <li>Top CB : {topCbText}</li>
      </ul>
    </div>
  );
};

export default Tooltip;