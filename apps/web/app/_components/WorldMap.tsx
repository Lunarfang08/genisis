"use client";

import type { WorldMap as WorldMapData } from "@/lib/shared-types";
import Link from "next/link";
import { useState } from "react";

export function WorldMap({
  data,
  worldId,
}: {
  data: WorldMapData;
  worldId: string;
}) {
  const [zoom, setZoom] = useState(1);
  const [selected, setSelected] = useState<string | null>(null);
  const [layer, setLayer] = useState<"population" | "economy">("population");
  const city = data.cities.find((item) => item.id === selected);

  return (
    <article className="map-panel observatory-panel">
      <header>
        <div>
          <span className="eyebrow">WORLD SURFACE / LIVE</span>
          <h2>Territory network</h2>
        </div>
        <div className="map-controls" aria-label="Map controls">
          <button
            onClick={() => setZoom((value) => Math.max(0.75, value - 0.25))}
            aria-label="Zoom out"
          >
            −
          </button>
          <output aria-live="polite">{Math.round(zoom * 100)}%</output>
          <button
            onClick={() => setZoom((value) => Math.min(2, value + 0.25))}
            aria-label="Zoom in"
          >
            +
          </button>
          <select
            value={layer}
            onChange={(event) =>
              setLayer(event.target.value as "population" | "economy")
            }
            aria-label="Map layer"
          >
            <option value="population">Population</option>
            <option value="economy">Economy</option>
          </select>
        </div>
      </header>
      <div className="city-map-viewport">
        <div className="city-map" style={{ transform: `scale(${zoom})` }}>
          {data.cities.map((item, index) => {
            const intensity =
              layer === "population"
                ? item.population
                : item.economic_activity_minor;
            return (
              <button
                className={`city-node ${selected === item.id ? "selected" : ""}`}
                key={item.id}
                onClick={() => setSelected(item.id)}
                style={{
                  left: `${10 + ((((item.longitude + 180) / 360) * 80 + index * 17) % 80)}%`,
                  top: `${12 + ((((90 - item.latitude) / 180) * 72 + index * 11) % 72)}%`,
                  width: `${Math.min(34, 12 + Math.log10(Math.max(1, intensity)) * 4)}px`,
                  height: `${Math.min(34, 12 + Math.log10(Math.max(1, intensity)) * 4)}px`,
                }}
                title={`${item.name}: ${item.population} citizens, ${item.businesses} businesses`}
              >
                <span>{item.name}</span>
              </button>
            );
          })}
          {!data.cities.length && (
            <p className="map-empty">
              Cities appear after world initialization.
            </p>
          )}
        </div>
      </div>
      <footer className="map-readout">
        {city ? (
          <>
            <div>
              <span>SELECTED CITY</span>
              <strong>{city.name}</strong>
            </div>
            <div>
              <span>POPULATION</span>
              <strong>{city.population.toLocaleString()}</strong>
            </div>
            <div>
              <span>BUSINESSES</span>
              <strong>{city.businesses.toLocaleString()}</strong>
            </div>
            <Link href={`/workspace/worlds/${worldId}?city=${city.id}`}>
              Open city dashboard →
            </Link>
          </>
        ) : (
          <span>Select a city node to inspect its live readout.</span>
        )}
        <div>
          <span>LANDMARKS / ACTIVITY</span>
          <strong>
            {data.landmarks.length} / {data.activity_events.length}
          </strong>
        </div>
      </footer>
    </article>
  );
}
