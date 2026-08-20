import { useEffect, useState } from "react";
import Carte from "./components/Carte";
import InfoPanel from "./components/InfoPanel";
import Legende from "./components/Legende";
import Slider from "./components/Slider";
import Tooltip from "./components/Tooltip";
import type { PrevisionGeoJSON, TooltipData } from "./types/geojson";

function App() {
  const [pointsData, setPointsData] = useState<PrevisionGeoJSON | null>(null);
  const [surfacesData, setSurfacesData] = useState<PrevisionGeoJSON | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [echeance, setEcheance] = useState<number>(0);
  const [tooltip, setTooltip] = useState<{ data: TooltipData; x: number; y: number } | null>(null);

  useEffect(() => {
    // La base URL est automatiquement configurée par Vite pour GitHub Pages
    const base = import.meta.env.BASE_URL;

    const fetchData = async () => {
      try {
        const [pointsResponse, surfacesResponse] = await Promise.all([
          fetch(`${base}previsions_orages_points.json`),
          fetch(`${base}previsions_orages_surfaces.json`),
        ]);

        if (!pointsResponse.ok || !surfacesResponse.ok) {
          throw new Error("Erreur lors du chargement des fichiers GeoJSON");
        }

        const points = (await pointsResponse.json()) as PrevisionGeoJSON;
        const surfaces = (await surfacesResponse.json()) as PrevisionGeoJSON;

        setPointsData(points);
        setSurfacesData(surfaces);

        if (points.metadata.echeances.length > 0) {
          // Sélectionne la première échéance qui contient des points
          const echeanceAvecPoints = points.metadata.echeances.find((e) =>
            points.features.some((f) => f.properties.echeance_h === e)
          );
          setEcheance(echeanceAvecPoints ?? points.metadata.echeances[0]);
        }
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erreur inconnue");
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleSurvol = (tooltipData: TooltipData | null, x: number, y: number) => {
    if (tooltipData) {
      setTooltip({ data: tooltipData, x, y });
    } else {
      setTooltip(null);
    }
  };

  return (
    <div className="app-container">
      <InfoPanel data={pointsData} loading={loading} error={error} />
      <Carte
        pointsData={pointsData}
        surfacesData={surfacesData}
        echeanceSelectionnee={echeance}
        onSurvol={handleSurvol}
      />
      <Legende />
      {pointsData && (
        <Slider
          echeances={pointsData.metadata.echeances}
          valeur={echeance}
          onChange={setEcheance}
        />
      )}
      {tooltip && <Tooltip data={tooltip.data} x={tooltip.x} y={tooltip.y} />}
    </div>
  );
}

export default App;