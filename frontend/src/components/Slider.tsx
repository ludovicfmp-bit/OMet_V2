// frontend/src/components/Slider.tsx

import React from "react";

interface SliderProps {
  echeances: number[];
  valeur: number;
  onChange: (echeance: number) => void;
}

const Slider: React.FC<SliderProps> = ({ echeances, valeur, onChange }) => {
  const indexActuel = echeances.indexOf(valeur);
  const min = 0;
  const max = echeances.length - 1;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value, 10);
    onChange(echeances[idx]);
  };

  return (
    <div className="slider-container">
      <label htmlFor="echeance-slider">
        Échéance : H+{valeur}
      </label>
      <input
        id="echeance-slider"
        type="range"
        min={min}
        max={max}
        step={1}
        value={indexActuel}
        onChange={handleChange}
      />
    </div>
  );
};

export default Slider;