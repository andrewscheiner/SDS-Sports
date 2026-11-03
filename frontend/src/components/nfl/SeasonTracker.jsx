import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from "recharts";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getSeason } from "@/lib/nfl";

const Stat = ({ label, value, tone, testid }) => (
  <div data-testid={testid}>
    <div className="text-[10px] uppercase tracking-[0.18em] text-[#718789]">{label}</div>
    <div className={`font-num text-2xl mt-1 ${tone || "text-white"}`}>{value}</div>
  </div>
);

const signed = (v, d = 2) => `${v >= 0 ? "+" : ""}${v.toFixed(d)}`;
const tone = (v) => (v >= 0 ? "text-[#ffb71b]" : "text-red-400");

export const SeasonTracker = ({ season }) => {
  const [minEv, setMinEv] = useState("0.04");
  const q = useQuery({ queryKey: ["season", season, minEv], queryFn: () => getSeason(season, minEv) });
  const d = q.data;
  return (
    <section data-testid="season-tracker" className="rounded-2xl bg-[#10282b] border border-white/[0.08] p-6 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow mb-2">Season tracker</p>
          <h2 className="text-base md:text-lg font-semibold">{season} model plays, graded at closing lines</h2>
        </div>
        <Tabs value={minEv} onValueChange={setMinEv}>
          <TabsList className="bg-[#071719] border border-white/10">
            {["0.02", "0.04", "0.08"].map((v) => (
              <TabsTrigger key={v} value={v} data-testid={`season-ev-${v}`}
                className="data-[state=active]:bg-[#ffb71b] data-[state=active]:text-[#071719]">
                {Math.round(v * 100)}%+ EV
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>
      {d && d.n_plays === 0 && <p className="text-sm text-[#718789]" data-testid="season-empty">No graded plays yet.</p>}
      {d && d.n_plays > 0 && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            <Stat testid="season-record" label="Record" value={`${d.total.win}-${d.total.loss}-${d.total.push}`} />
            <Stat testid="season-units" label="Units" value={`${signed(d.total.units)}u`} tone={tone(d.total.units)} />
            <Stat testid="season-roi" label="ROI" value={`${signed(d.total.roi * 100, 1)}%`} tone={tone(d.total.roi)} />
            <Stat testid="season-plays" label="Plays" value={d.n_plays} />
          </div>
          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            <div className="h-56" data-testid="season-chart">
              <ResponsiveContainer>
                <AreaChart data={d.by_week} margin={{ left: -20, right: 8, top: 8 }}>
                  <defs>
                    <linearGradient id="u" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ffb71b" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#ffb71b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="week" tickFormatter={(w) => `W${w}`} stroke="#718789" fontSize={11} />
                  <YAxis stroke="#718789" fontSize={11} />
                  <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" />
                  <Tooltip contentStyle={{ background: "#071719", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                    formatter={(v) => [`${signed(v)}u`, "Cumulative"]} labelFormatter={(w) => `Week ${w}`} />
                  <Area dataKey="cum_units" stroke="#ffb71b" strokeWidth={2} fill="url(#u)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2 text-sm" data-testid="season-by-market">
              {d.by_market.map((m) => (
                <div key={m.market} className="grid grid-cols-[5.5rem_1fr_4.5rem] items-center border-b border-white/[0.06] pb-2">
                  <span className="text-[#a9b9ba]">{m.label}</span>
                  <span className="font-num text-[#718789]">{m.win}-{m.loss}-{m.push}</span>
                  <span className={`font-num text-right ${tone(m.units)}`}>{signed(m.units)}u</span>
                </div>
              ))}
            </div>
          </div>
          {!d.odds_sources.includes("live") && (
            <p className="text-xs text-[#718789]" data-testid="season-sample-note">
              Graded against SAMPLE odds until a real Odds API key is added — these results are not real.
            </p>
          )}
        </>
      )}
    </section>
  );
};
