// frontend/src/components/Carte.tsx
import type { PrevisionGeoJSON, TooltipData } from "../types/geojson";
import React, { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";


interface CarteProps {
  pointsData: PrevisionGeoJSON | null;
  surfacesData: PrevisionGeoJSON | null;
  echeanceSelectionnee: number;
  onSurvol: (data: TooltipData | null, x: number, y: number) => void;
}

const COULEURS_RISQUE: Record<number, string> = {
  1: "#FFD34E",
  2: "#FF9F1C",
  3: "#E63946",
  4: "#A855F7",
};

const Carte: React.FC<CarteProps> = ({
  pointsData,
  surfacesData,
  echeanceSelectionnee,
  onSurvol,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [cartePrete, setCartePrete] = useState(false);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm-tiles",
            type: "raster",
            source: "osm",
            paint: {
              "raster-brightness-min": 0.1,
              "raster-brightness-max": 0.5,
              "raster-saturation": -0.8,
            },
          },
        ],
      },
      center: [2.0, 46.0],
      zoom: 5.5,
      minZoom: 4,
      maxZoom: 9,
    });

    map.current.addControl(new maplibregl.NavigationControl(), "top-right");

    map.current.on("load", () => {
      setCartePrete(true);
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!map.current || !cartePrete || !pointsData || !surfacesData) return;

    const mapInstance = map.current;

    // Filtrer les features pour l'échéance sélectionnée
    const pointsFeatures = pointsData.features.filter(
      (f) => f.properties.echeance_h === echeanceSelectionnee
    );
    const surfacesFeatures = surfacesData.features.filter(
      (f) => f.properties.echeance_h === echeanceSelectionnee
    );

    const pointsGeoJSON = {
  type: "FeatureCollection",
  features: pointsFeatures,
} as PrevisionGeoJSON;

const surfacesGeoJSON = {
  type: "FeatureCollection",
  features: surfacesFeatures,
} as PrevisionGeoJSON;

    // Source des surfaces
    const surfaceSourceId = "surfaces-previsions";
    if (mapInstance.getSource(surfaceSourceId)) {
      (mapInstance.getSource(surfaceSourceId) as maplibregl.GeoJSONSource).setData(surfacesGeoJSON);
    } else {
      mapInstance.addSource(surfaceSourceId, {
        type: "geojson",
        data: surfacesGeoJSON,
      });
    }

    // Source des points (pour tooltip)
    const pointSourceId = "points-tooltip";
    if (mapInstance.getSource(pointSourceId)) {
      (mapInstance.getSource(pointSourceId) as maplibregl.GeoJSONSource).setData(pointsGeoJSON);
    } else {
      mapInstance.addSource(pointSourceId, {
        type: "geojson",
        data: pointsGeoJSON,
      });
    }

    // Couche visible : surfaces (fill)
    const surfaceLayerId = "surface-risque";
    if (!mapInstance.getLayer(surfaceLayerId)) {
      mapInstance.addLayer({
        id: surfaceLayerId,
        type: "fill",
        source: surfaceSourceId,
        filter: [">", ["get", "risque"], 0],
        paint: {
          "fill-color": [
            "match",
            ["get", "risque"],
            1, COULEURS_RISQUE[1],
            2, COULEURS_RISQUE[2],
            3, COULEURS_RISQUE[3],
            4, COULEURS_RISQUE[4],
            "transparent",
          ],
          "fill-opacity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            4, 0.50,
            6, 0.60,
            8, 0.72,
            10, 0.78,
          ],
          "fill-outline-color": "rgba(0,0,0,0)",
        },
      });
    }

    // Couche de points invisible pour le tooltip
    const pointLayerId = "points-tooltip-layer";
    if (!mapInstance.getLayer(pointLayerId)) {
      mapInstance.addLayer({
        id: pointLayerId,
        type: "circle",
        source: pointSourceId,
        paint: {
          "circle-radius": 12,
          "circle-color": "rgba(0,0,0,0)",
          "circle-opacity": 0,
          "circle-stroke-width": 0,
        },
      });
    }

    // Gestion du survol sur les points invisibles
    const handleMouseMove = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
      const feature = e.features && e.features[0];
      if (feature) {
        const props = feature.properties as TooltipData;
        onSurvol(props, e.point.x, e.point.y);
      } else {
        onSurvol(null, 0, 0);
      }
    };

    const handleMouseLeave = () => {
      onSurvol(null, 0, 0);
    };

    mapInstance.on("mousemove", pointLayerId, handleMouseMove);
    mapInstance.on("mouseleave", pointLayerId, handleMouseLeave);

    return () => {
      mapInstance.off("mousemove", pointLayerId, handleMouseMove);
      mapInstance.off("mouseleave", pointLayerId, handleMouseLeave);
    };
  }, [pointsData, surfacesData, echeanceSelectionnee, cartePrete, onSurvol]);

  return <div ref={mapContainer} className="map-container" />;
};

export default Carte;