// frontend/src/components/Legende.tsx

import React from "react";

const NIVEAUX = [
  { niveau: 0, label: "Pas d'orage", couleur: "transparent" },
  { niveau: 1, label: "Activité possible", couleur: "#ffd700" },
  { niveau: 2, label: "Orages probables", couleur: "#ffa500" },
  { niveau: 3, label: "Orages forts", couleur: "#dc143c" },
  { niveau: 4, label: "Orages violents", couleur: "#9400d3" },
];

const Legende: React.FC = () => {
  return (
    <div className="legende">
      <h4>Risque orageux</h4>
      {NIVEAUX.map((item) => (
        <div key={item.niveau} className="legende-item">
          <span
            className="legende-color"
            style={{
              backgroundColor: item.couleur,
              border: item.niveau === 0 ? "1px solid #666" : undefined,
            }}
          />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
};

export default Legende;