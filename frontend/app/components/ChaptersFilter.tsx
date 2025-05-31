// app/components/ChaptersFilter.tsx
import { useState, useEffect } from "react";

interface ChaptersFilterProps {
  maxChapters: number;
  currentRange: [number, number];
  onRangeChange: (range: [number, number]) => void;
}

export default function ChaptersFilter({
  maxChapters,
  currentRange,
  onRangeChange,
}: ChaptersFilterProps) {
  const [minVal, setMinVal] = useState(currentRange[0]);
  const [maxVal, setMaxVal] = useState(currentRange[1]);

  useEffect(() => {
    setMinVal(currentRange[0]);
    setMaxVal(currentRange[1]);
  }, [currentRange]);

  const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.min(Number(e.target.value), maxVal - 1);
    setMinVal(value);
    onRangeChange([value, maxVal]);
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.max(Number(e.target.value), minVal + 1);
    setMaxVal(value);
    onRangeChange([minVal, value]);
  };

  return (
    <div>
      <h3 className="text-md font-semibold mb-2 text-slate-600">Chapters</h3>
      <div className="flex items-center space-x-2 text-sm text-slate-500 mb-1">
        <span>{minVal}</span>
        <span className="flex-grow text-center">to</span>
        <span>{maxVal}</span>
      </div>
      <div className="relative pt-1">
        <input
          type="range"
          min="0"
          max={maxChapters}
          value={minVal}
          onChange={handleMinChange}
          className="absolute w-full h-1 bg-transparent appearance-none pointer-events-none z-10"
          style={{ zIndex: minVal > maxChapters - 10 ? 5 : undefined }} // Ensure min thumb is on top if values are close
        />
        <input
          type="range"
          min="0"
          max={maxChapters}
          value={maxVal}
          onChange={handleMaxChange}
          className="absolute w-full h-1 bg-transparent appearance-none pointer-events-none z-10"
        />
        {/* Track background */}
        <div className="relative w-full h-1 bg-slate-200 rounded-md">
          {/* Highlighted range */}
          <div
            className="absolute h-1 bg-sky-500 rounded-md"
            style={{
              left: `${(minVal / maxChapters) * 100}%`,
              width: `${((maxVal - minVal) / maxChapters) * 100}%`,
            }}
          ></div>
        </div>
      </div>
    </div>
  );
}
