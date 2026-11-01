import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";

export const DashHeader = ({ meta }) => {
  const live = meta?.odds_sources?.includes("live");
  return (
    <header className="border-b border-[#D4AF37]/20 bg-[#04120B]" data-testid="dash-header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="flex items-center gap-3 text-xs uppercase tracking-[0.25em] text-emerald-400/80">
          <Activity className="h-4 w-4 text-[#E5C158]" />
          <span>Scheiner Digital Solutions</span>
          <span className="text-emerald-300/70">/ sports / nfl</span>
        </div>
        <div className="mt-5 flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div className="rise">
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight">
              First Quarter <span className="text-[#E5C158]">&amp;</span> First Half
            </h1>
            <p className="mt-3 text-sm sm:text-base text-emerald-100/60 max-w-xl">
              XGBoost score projections for every game, priced against seven sportsbooks.
            </p>
          </div>
          {meta && (
            <div className="flex flex-wrap items-center gap-3">
              <Badge
                data-testid="odds-source-badge"
                className={live ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/40" : "bg-[#E5C158]/10 text-[#E5C158] border border-[#E5C158]/40"}
              >
                {live ? "Live odds" : "Sample odds"}
              </Badge>
              <Badge data-testid="season-week-badge" className="bg-[#0A2216] text-emerald-100 border border-emerald-800">
                {meta.season} · Week {meta.current_week}
              </Badge>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
