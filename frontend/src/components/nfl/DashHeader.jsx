import { Badge } from "@/components/ui/badge";
import { Activity } from "lucide-react";

export const DashHeader = ({ meta }) => {
  const live = meta?.odds_sources?.includes("live");
  return (
    <header data-testid="dash-header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[88px] flex items-center justify-between">
        <a href="/" className="flex items-center gap-3 text-white no-underline" data-testid="brand-link">
          <Activity className="h-6 w-6 text-[#ffb71b]" />
          <span className="text-[1.05rem] font-[650]">Scheiner Digital Solutions</span>
        </a>
        <nav className="nav flex items-center gap-7">
          <span className="text-[#b8c5c6] text-[0.92rem] hidden sm:inline">Sports</span>
          <span className="nav-contact text-[0.92rem]" data-testid="nav-nfl">NFL</span>
        </nav>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-6">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div className="rise">
            <p className="eyebrow mb-5">SDS Sports · NFL Model</p>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-[0.98] tracking-[-0.05em]">
              First Quarter <span className="text-[#ffb71b]">&amp;</span> First Half
            </h1>
            <p className="mt-6 text-base sm:text-lg leading-relaxed text-[#a9b9ba] max-w-xl">
              XGBoost score projections for every game, priced against DraftKings, FanDuel, BetMGM and ESPN BET.
            </p>
          </div>
          {meta && (
            <div className="flex flex-wrap items-center gap-3">
              <Badge
                data-testid="odds-source-badge"
                className={live ? "bg-[#00636b]/30 text-teal-300 border border-[#008a92]/60" : "bg-[#ffb71b]/10 text-[#ffb71b] border border-[#ffb71b]/40"}
              >
                {live ? "Live odds" : "Sample odds"}
              </Badge>
              <Badge data-testid="season-week-badge" className="bg-[#10282b] text-[#a9b9ba] border border-white/10">
                {meta.season} · Week {meta.current_week}
              </Badge>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
