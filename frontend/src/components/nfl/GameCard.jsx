import { Button } from "@/components/ui/button";
import { betLabel, fmtEv, fmtPoint, kickoff } from "@/lib/nfl";

const ScoreRow = ({ team, qb, pred, actual, testid }) => (
  <div className="grid grid-cols-[1fr_4.5rem_4.5rem] items-center py-2" data-testid={testid}>
    <div>
      <span className="font-display text-xl font-bold">{team}</span>
      {qb && <span className="ml-2 text-xs text-[#718789]">{qb}</span>}
    </div>
    {["q1", "h1"].map((p, i) => (
      <div key={p} className="text-right font-num">
        <span className="text-lg text-[#ffb71b]">{pred[p].toFixed(1)}</span>
        {actual && <span className="block text-[11px] text-[#718789]">final {actual[p]}</span>}
      </div>
    ))}
  </div>
);

export const GameCard = ({ game: g, index, period, minEv, onOpen }) => {
  const side = (i) => ({ q1: g.pred.q1[i], h1: g.pred.h1[i] });
  const act = (i) => g.actual && { q1: g.actual.q1[i], h1: g.actual.h1[i] };
  const best = g.edges
    .filter((e) => period === "all" || e.market.startsWith(period))
    .reduce((b, e) => (!b || e.ev > b.ev ? e : b), null);
  const hot = best && best.ev >= Math.max(minEv, 0.08);
  const fair = (p) => `${g.home_team} ${fmtPoint(-Math.round(g.fair[p].margin * 2) / 2 || 0)} · O/U ${(Math.round(g.fair[p].total * 2) / 2).toFixed(1)}`;

  return (
    <article data-testid={`game-card-${g.game_id}`} style={{ animationDelay: `${index * 40}ms` }}
      className={`rise rounded-2xl bg-[#10282b] border border-[#ffb71b]/15 p-5 flex flex-col ${hot ? "gold-edge" : ""}`}>
      <div className="flex justify-between text-[11px] uppercase tracking-widest text-[#718789]">
        <span>{kickoff(g.gameday, g.gametime)}</span>
        <span className="font-num">{g.home_team} {fmtPoint(-g.spread_line)} · {g.total_line}</span>
      </div>
      <div className="mt-3 grid grid-cols-[1fr_4.5rem_4.5rem] text-[11px] uppercase tracking-widest text-[#718789]">
        <span /><span className="text-right">Q1</span><span className="text-right">1H</span>
      </div>
      <div className="divide-y divide-white/10">
        <ScoreRow team={g.away_team} qb={g.away_qb} pred={side(1)} actual={act(1)} testid={`away-row-${g.game_id}`} />
        <ScoreRow team={g.home_team} qb={g.home_qb} pred={side(0)} actual={act(0)} testid={`home-row-${g.game_id}`} />
      </div>
      <div className="mt-3 space-y-1 text-xs text-[#718789] font-num">
        <div>Q1 fair: {fair("q1")}</div>
        <div>1H fair: {fair("h1")}</div>
      </div>
      <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between gap-3">
        {best ? (
          <div data-testid={`best-edge-${g.game_id}`} className="text-sm">
            <span className="text-[#718789] text-xs mr-1">{best.market_label}</span>
            <span className="font-semibold">{betLabel(best)}</span>
            <span className={`ml-2 font-num font-bold ${best.ev > 0 ? "text-[#ffb71b]" : "text-[#718789]"}`}>{fmtEv(best.ev)}</span>
          </div>
        ) : <span className="text-xs text-[#718789]">No odds</span>}
        <Button size="sm" variant="ghost" onClick={onOpen} data-testid={`compare-books-${g.game_id}`}
          className="text-[#ffb71b] hover:bg-[#ffb71b]/10 hover:text-[#ffc33d] shrink-0">
          Compare books
        </Button>
      </div>
    </article>
  );
};
