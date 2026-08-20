// frontend/src/components/InfoPanel.tsx

import React from "react";
import type { PrevisionGeoJSON } from "../types/geojson";

interface InfoPanelProps {
  data: PrevisionGeoJSON | null;
  loading: boolean;
  error: string | null;
}

const InfoPanel: React.FC<InfoPanelProps> = ({ data, loading, error }) => {
  if (loading) {
    return (
      <div className="info-panel">
        <p>Chargement des données…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="info-panel">
        <p style={{ color: "#ff5555" }}>Erreur : {error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="info-panel">
        <p>Aucune donnée disponible.</p>
      </div>
    );
  }

  const { metadata } = data;
  return (
    <div className="info-panel">
      <h3>Prévisions orageuses</h3>
      <p>
        Cycle ICON-EU : <strong>{metadata.cycle_icon_eu}</strong> ({metadata.date_run})
      </p>
      <p>Généré le : {metadata.genere_le}</p>
      <p className="avertissement">{metadata.avertissement}</p>
    </div>
  );
};

export default InfoPanel;