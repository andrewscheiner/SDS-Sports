import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";

const Stat = ({ label, value, sub, testid }) => (
  <div data-testid={testid} className="rounded-md bg-[#04120B] border border-emerald-900 p-4">
    <div className="text-[10px] uppercase tracking-widest text-emerald-400/70">{label}</div>
    <div className="font-num text-2xl text-[#E5C158] mt-1">{value}</div>
    {sub && <div className="text-xs text-emerald-100/50 mt-1">{sub}</div>}
  </div>
);

export const ModelPanel = ({ meta }) => {
  const max = meta.importance[0]?.value || 1;
  const { pts_q1: q1, pts_h1: h1 } = meta.metrics;
  return (
    <Collapsible defaultOpen className="rounded-lg bg-[#0A2216] border border-[#D4AF37]/15" data-testid="model-panel">
      <CollapsibleTrigger data-testid="model-panel-toggle" className="w-full flex items-center justify-between p-5 group">
        <h2 className="font-display text-base md:text-lg font-semibold">Model</h2>
        <ChevronDown className="h-4 w-4 text-[#E5C158] transition-transform group-data-[state=open]:rotate-180" />
      </CollapsibleTrigger>
      <CollapsibleContent className="px-5 pb-6 grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-4">
          <p className="text-sm text-emerald-100/60">
            Two XGBoost regressors (team Q1 and 1H points) trained on {meta.train_start}–{meta.season} play-by-play
            from nflreadpy, retrained weekly with no look-ahead. Probabilities come from simulating
            backtest residuals around each projection. Projections are blended 50/50 with the Vegas-implied
            share, so edges reflect where the model disagrees with the market — treat small edges as noise.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <Stat testid="mae-q1" label="Q1 MAE / team" value={q1.mae.toFixed(2)} sub={`Vegas-share baseline ${q1.baseline_mae.toFixed(2)}`} />
            <Stat testid="mae-h1" label="1H MAE / team" value={h1.mae.toFixed(2)} sub={`Vegas-share baseline ${h1.baseline_mae.toFixed(2)}`} />
          </div>
          <p className="text-xs text-emerald-100/40">
            Backtest {meta.backtest_seasons.join(", ")} · {meta.n_train_rows.toLocaleString()} team-games · trained {new Date(meta.trained_at).toLocaleString()}
          </p>
        </div>
        <div data-testid="feature-importance" className="space-y-2">
          <div className="text-[10px] uppercase tracking-widest text-emerald-400/70">Top features (1H model)</div>
          {meta.importance.map((f) => (
            <div key={f.feature} className="grid grid-cols-[11rem_1fr] items-center gap-3 text-xs">
              <span className="text-emerald-100/70 truncate">{f.label}</span>
              <div className="h-2 rounded-full bg-[#04120B]">
                <div className="h-2 rounded-full bg-[#D4AF37]" style={{ width: `${(f.value / max) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};
