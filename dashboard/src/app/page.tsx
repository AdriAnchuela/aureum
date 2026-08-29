import LineChart from "@/components/LineChart";
import OddsTable from "@/components/OddsTable";
import Panel from "@/components/Panel";
import StatTile from "@/components/StatTile";
import {
  fetchIntraday,
  fetchMacro,
  fetchOdds,
  fetchPositioning,
  fetchRisk,
} from "@/lib/api";

export const dynamic = "force-dynamic";

const usd = (v: number) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
const pct = (v: number) => `${v.toFixed(2)}%`;

export default async function Home() {
  const [macro, intraday, risk, positioning, odds] = await Promise.all([
    fetchMacro(),
    fetchIntraday(),
    fetchRisk(),
    fetchPositioning(),
    fetchOdds(),
  ]);

  const lastMacro = macro?.at(-1);
  const lastPos = positioning?.at(-1);
  const cleanRisk = (risk ?? []).filter((r) => r.n_events >= 100);
  const fedMarket = odds?.find((o) => o.question.toLowerCase().includes("fed"));

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <header className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            AUREUM<span style={{ color: "var(--gold)" }}>.</span>
          </h1>
          <p className="text-xs" style={{ color: "var(--muted)" }}>
            macro intelligence · explains, never predicts
          </p>
        </div>
        {lastMacro && (
          <div className="text-right">
            <div className="num text-3xl font-bold" style={{ color: "var(--gold)" }}>
              {usd(lastMacro.gold_usd)}
            </div>
            <div className="text-[11px]" style={{ color: "var(--muted)" }}>
              gold futures · {lastMacro.date.slice(0, 10)}
            </div>
          </div>
        )}
      </header>

      {!macro && (
        <div className="card mb-4 p-4 text-sm" style={{ color: "var(--ink-2)" }}>
          API offline — start it with <code>make api</code> (port 8010).
        </div>
      )}

      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <StatTile
          label="Gold 1d"
          value={lastMacro ? usd(lastMacro.gold_usd) : "—"}
          delta={lastMacro?.gold_return_1d}
        />
        <StatTile
          label="10y real yield"
          value={lastMacro?.real_yield_10y != null ? pct(lastMacro.real_yield_10y) : "—"}
          hint="TIPS, FRED"
        />
        <StatTile
          label="Curve 10y–2y"
          value={lastMacro?.curve_10y_2y != null ? pct(lastMacro.curve_10y_2y) : "—"}
          hint={lastMacro?.curve_10y_2y != null && lastMacro.curve_10y_2y < 0 ? "inverted" : "normal"}
        />
        <StatTile
          label="VIX"
          value={lastMacro?.vix != null ? lastMacro.vix.toFixed(1) : "—"}
        />
        <StatTile
          label="Specs net gold"
          value={lastPos?.net_share_oi != null ? `${(lastPos.net_share_oi * 100).toFixed(0)}% OI` : "—"}
          hint={lastPos?.positioning_zscore_3y != null ? `z = ${lastPos.positioning_zscore_3y.toFixed(2)} (3y)` : undefined}
        />
        <StatTile
          label="Fed next meeting"
          value={fedMarket ? `${Math.round(fedMarket.leading_prob * 100)}%` : "—"}
          hint={fedMarket ? fedMarket.leading_outcome : "Polymarket"}
        />
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <Panel title="Gold, 1y" sub="daily close · Yahoo GC=F">
          <LineChart
            data={(macro ?? []).map((d) => ({ t: d.date, v: d.gold_usd }))}
            color="var(--gold)"
            area
            yKind="usd"
          />
        </Panel>
        <Panel title="10y real yield, 1y" sub="the anti-gold force · FRED DFII10">
          <LineChart
            data={(macro ?? [])
              .filter((d) => d.real_yield_10y != null)
              .map((d) => ({ t: d.date, v: d.real_yield_10y as number }))}
            color="var(--blue)"
            yKind="pct"
          />
        </Panel>
        <Panel title="Gold 24/7 · PAXG stream" sub="1-min bars, live via Redpanda">
          <LineChart
            data={(intraday ?? []).map((d) => ({ t: d.minute, v: d.close }))}
            color="var(--gold)"
            yKind="usd"
            tKind="time"
            emptyLabel="stream is young — run `aureum stream paxg` to fill this"
          />
        </Panel>
        <Panel title="Speculative positioning, gold" sub="net non-commercial z-score · CFTC COT">
          <LineChart
            data={(positioning ?? [])
              .filter((d) => d.positioning_zscore_3y != null)
              .map((d) => ({ t: d.report_date, v: d.positioning_zscore_3y as number }))}
            color="var(--aqua)"
            zeroBaseline
            yKind="z"
          />
        </Panel>
        <Panel title="Geopolitical pressure" sub="conflict share of coverage · GDELT">
          <LineChart
            data={cleanRisk.map((d) => ({
              t: d.event_date,
              v: (d.conflict_article_share ?? 0) * 100,
            }))}
            color="var(--red)"
            yKind="pctInt"
            emptyLabel="accumulating GDELT history — one file every 15 min"
          />
        </Panel>
        <Panel title="Prediction markets" sub="macro events · Polymarket 24h volume">
          {odds ? <OddsTable rows={odds.slice(0, 8)} /> : <span className="text-xs" style={{ color: "var(--muted)" }}>—</span>}
        </Panel>
      </div>

      <footer className="mt-6 text-[11px] leading-relaxed" style={{ color: "var(--muted)" }}>
        AUREUM observes, correlates and explains. It does not execute trades, recommend positions,
        or constitute investment advice. Sources: Yahoo Finance, FRED, CFTC, GDELT, Polymarket,
        Binance (PAXG). Part of the{" "}
        <a href="https://github.com/AdriAnchuela/aureum" className="underline">
          aureum
        </a>{" "}
        open project.
      </footer>
    </main>
  );
}
