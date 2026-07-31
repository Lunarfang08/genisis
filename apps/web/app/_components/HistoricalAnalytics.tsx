import type { Analytics } from "@/lib/shared-types";

function sparkline(points: Array<{ value: number }>) {
  if (!points.length) return "";
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const range = Math.max(1, Math.max(...values) - min);
  return points
    .map(
      (point, index) =>
        `${(index / Math.max(1, points.length - 1)) * 100},${38 - ((point.value - min) / range) * 34}`,
    )
    .join(" ");
}

export function HistoricalAnalytics({ data }: { data: Analytics }) {
  return (
    <section className="analytics-grid" aria-label="Historical analytics">
      {data.series.slice(0, 4).map((series) => (
        <article className="analytics-card" key={series.name}>
          <span>{series.name.replaceAll("_", " ")}</span>
          <strong>{series.points.at(-1)?.value.toLocaleString() ?? "—"}</strong>
          <small>{series.unit}</small>
          <svg
            viewBox="0 0 100 40"
            role="img"
            aria-label={`${series.name} history`}
            preserveAspectRatio="none"
          >
            <polyline points={sparkline(series.points)} />
          </svg>
        </article>
      ))}
      {!data.series.length && (
        <div className="analytics-empty">
          <strong>No historical metrics yet.</strong>
          <span>
            Charts populate from committed world metrics after simulation ticks.
          </span>
        </div>
      )}
    </section>
  );
}
