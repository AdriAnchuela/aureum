"use client";

import { useId, useMemo, useRef, useState } from "react";

type Point = { t: string; v: number };

type YKind = "usd" | "pct" | "pctInt" | "z";
type TKind = "date" | "time";

type Props = {
  data: Point[];
  color: string;
  height?: number;
  yKind?: YKind;
  tKind?: TKind;
  area?: boolean;
  zeroBaseline?: boolean;
  emptyLabel?: string;
};

const Y_FMT: Record<YKind, (v: number) => string> = {
  usd: (v) => `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`,
  pct: (v) => `${v.toFixed(2)}%`,
  pctInt: (v) => `${v.toFixed(0)}%`,
  z: (v) => v.toFixed(1),
};

const T_FMT: Record<TKind, (t: string) => string> = {
  date: (t) => t.slice(5, 10),
  time: (t) => t.slice(11, 16),
};

const W = 640;
const M = { top: 14, right: 64, bottom: 22, left: 8 };

export default function LineChart({
  data,
  color,
  height = 220,
  yKind = "pct",
  tKind = "date",
  area = false,
  zeroBaseline = false,
  emptyLabel = "awaiting data…",
}: Props) {
  const yFmt = Y_FMT[yKind];
  const tFmt = T_FMT[tKind];
  const H = height;
  const ref = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);
  const gradId = useId();

  const scale = useMemo(() => {
    if (data.length < 2) return null;
    const vs = data.map((d) => d.v);
    let lo = Math.min(...vs);
    let hi = Math.max(...vs);
    if (zeroBaseline) {
      lo = Math.min(lo, 0);
      hi = Math.max(hi, 0);
    }
    const pad = (hi - lo || Math.abs(hi) || 1) * 0.08;
    const vLo = lo - pad;
    const vHi = hi + pad;
    const x = (i: number) => M.left + (i / (data.length - 1)) * (W - M.left - M.right);
    const y = (v: number) => M.top + (1 - (v - vLo) / (vHi - vLo)) * (H - M.top - M.bottom);
    const ticks = Array.from({ length: 4 }, (_, k) => {
      const v = lo + ((hi - lo) * k) / 3;
      return { v, y: y(v) };
    });
    return { xs: data.map((_, i) => x(i)), ys: data.map((d) => y(d.v)), ticks, y0: y(0) };
  }, [data, H, zeroBaseline]);

  if (!scale)
    return (
      <div
        className="flex items-center justify-center text-xs"
        style={{ color: "var(--muted)", height }}
      >
        {emptyLabel}
      </div>
    );

  const { xs, ys, ticks, y0 } = scale;
  const last = data.length - 1;
  const cursor = hover ?? last;
  const path = xs.map((x, i) => `${i ? "L" : "M"}${x.toFixed(1)},${ys[i].toFixed(1)}`).join("");

  return (
    <div className="relative">
      <svg
        ref={ref}
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        onPointerMove={(e) => {
          const box = ref.current?.getBoundingClientRect();
          if (!box) return;
          const fx = ((e.clientX - box.left) / box.width) * W;
          const i = Math.round(((fx - M.left) / (W - M.left - M.right)) * last);
          setHover(Math.max(0, Math.min(last, i)));
        }}
        onPointerLeave={() => setHover(null)}
      >
        {ticks.map((tk, i) => (
          <g key={i}>
            <line x1={M.left} x2={W - M.right} y1={tk.y} y2={tk.y} stroke="var(--grid)" strokeWidth="1" />
            <text x={W - M.right + 8} y={tk.y + 3} fontSize="10" fill="var(--muted)" className="num">
              {yFmt(tk.v)}
            </text>
          </g>
        ))}
        {zeroBaseline && (
          <line x1={M.left} x2={W - M.right} y1={y0} y2={y0} stroke="var(--baseline)" strokeWidth="1" strokeDasharray="4 4" />
        )}
        {area && (
          <>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity="0.18" />
                <stop offset="100%" stopColor={color} stopOpacity="0" />
              </linearGradient>
            </defs>
            <path d={`${path}L${xs[last]},${H - M.bottom}L${xs[0]},${H - M.bottom}Z`} fill={`url(#${gradId})`} />
          </>
        )}
        <path d={path} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
        {hover !== null && (
          <line x1={xs[cursor]} x2={xs[cursor]} y1={M.top} y2={H - M.bottom} stroke="var(--baseline)" strokeWidth="1" />
        )}
        <circle cx={xs[cursor]} cy={ys[cursor]} r="4" fill={color} stroke="var(--surface)" strokeWidth="2" />
        <text x={M.left} y={H - 6} fontSize="10" fill="var(--muted)">
          {tFmt(data[0].t)}
        </text>
        <text x={W - M.right} y={H - 6} fontSize="10" fill="var(--muted)" textAnchor="end">
          {tFmt(data[last].t)}
        </text>
      </svg>
      {hover !== null && (
        <div
          className="card pointer-events-none absolute px-2 py-1 text-xs whitespace-nowrap"
          style={{ left: `${(xs[cursor] / W) * 100}%`, top: 0, transform: "translateX(-50%)" }}
        >
          <span style={{ color: "var(--muted)" }}>{tFmt(data[cursor].t)}</span>{" "}
          <span className="num">{yFmt(data[cursor].v)}</span>
        </div>
      )}
    </div>
  );
}
