// frontend/src/types/geojson.ts

export interface PrevisionFeature {
  type: "Feature";
  geometry: {
    type: "Point" | "Polygon";
    coordinates: number[] | number[][][]; // Point : [lon, lat], Polygon : [[[lon, lat], ...]]
  };
  properties: {
    echeance_h: number;
    cape_ml_jkg?: number | null;
    precip_mm_h?: number | null;
    score?: number | null;
    risque: number;
    top_cb_fl?: number;
  };
}

export interface PrevisionGeoJSON {
  type: "FeatureCollection";
  metadata: {
    genere_le: string;
    modele: string;
    cycle_icon_eu: string;
    date_run: string;
    zone: {
      lon_min: number;
      lon_max: number;
      lat_min: number;
      lat_max: number;
    };
    echeances: number[];
    grid_step: number;
    formule: string;
    avertissement: string;
  };
  features: PrevisionFeature[];
}

export interface TooltipData {
  echeance_h: number;
  cape_ml_jkg: number | null;
  precip_mm_h: number | null;
  score: number | null;
  risque: number;
  top_cb_fl: number;
}