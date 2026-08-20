# Prévisions orageuses ICON-EU

Application web affichant des prévisions de risque orageux sur la France et les pays voisins à partir du modèle météorologique ICON-EU (DWD).

## Architecture

- **backend/** : script Python pour télécharger les GRIB2, calculer l'indice de risque et générer le GeoJSON.
- **data/** : fichier de prévisions généré (`previsions_orages.json`).
- **frontend/** : application React + MapLibre GL pour l'affichage interactif.
- **.github/workflows/** : workflow de mise à jour automatique toutes les 3 heures.

## Avertissement

Prévision expérimentale, ne remplace pas les vigilances officielles de Météo-France ou d'autres organismes.

## Statut

En cours de développement.