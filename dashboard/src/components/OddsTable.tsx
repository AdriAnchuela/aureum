import type { EventOdds } from "@/lib/api";

const money = (v: number) =>
  v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : `$${Math.round(v / 1e3)}k`;

export default function OddsTable({ rows }: { rows: EventOdds[] }) {
  return (
    <div className="flex flex-col gap-1.5">
      {rows.map((r) => (
        <div key={r.market_id} className="grid grid-cols-[1fr_auto] items-center gap-3 py-1">
          <div className="min-w-0">
            <div className="truncate text-sm" title={r.question}>
              {r.question}
            </div>
            <div className="mt-1 flex items-center gap-2">
              <div className="h-1.5 w-full max-w-56 overflow-hidden rounded-full" style={{ background: "var(--grid)" }}>
                <div
                  className="h-full rounded-full"
                  style={{ width: `${r.leading_prob * 100}%`, background: "var(--blue)" }}
                />
              </div>
              <span className="text-[11px]" style={{ color: "var(--muted)" }}>
                {money(r.volume_24h)} · 24h
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className="num text-sm font-semibold">{Math.round(r.leading_prob * 100)}%</span>
            <span className="ml-1.5 text-xs" style={{ color: "var(--ink-2)" }}>
              {r.leading_outcome}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
