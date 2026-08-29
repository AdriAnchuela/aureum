type Props = {
  label: string;
  value: string;
  delta?: number | null;
  deltaFmt?: (d: number) => string;
  hint?: string;
};

export default function StatTile({ label, value, delta, deltaFmt, hint }: Props) {
  const fmt = deltaFmt ?? ((d: number) => `${d >= 0 ? "+" : ""}${(d * 100).toFixed(2)}%`);
  return (
    <div className="card px-4 py-3">
      <div className="text-[11px] uppercase tracking-wider" style={{ color: "var(--muted)" }}>
        {label}
      </div>
      <div className="num mt-1 text-xl font-semibold">{value}</div>
      {delta !== undefined && delta !== null && (
        <div className="num mt-0.5 text-xs" style={{ color: delta >= 0 ? "var(--good)" : "var(--red)" }}>
          {delta >= 0 ? "▲" : "▼"} {fmt(delta)}
        </div>
      )}
      {hint && (
        <div className="mt-0.5 text-[11px]" style={{ color: "var(--muted)" }}>
          {hint}
        </div>
      )}
    </div>
  );
}
