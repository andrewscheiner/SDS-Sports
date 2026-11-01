import { betLabel, fmtEv, fmtPrice, fmtPct } from "@/lib/nfl";

const RESULT = { win: "text-emerald-400", loss: "text-red-400", push: "text-emerald-100/50" };

export const TopEdges = ({ edges, record, period, minEv, onOpen }) => {
  const list = edges.filter((e) => e.ev >= minEv && (period === "all" || e.market.startsWith(period))).slice(0, 6);
  const graded = record.win + record.loss + record.push > 0;
  return (
    <section data-testid="top-edges" className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="font-display text-base md:text-lg font-semibold">Top edges this week</h2>
        {graded && (
          <p data-testid="week-record" className="text-xs text-emerald-100/60">
            +4% EV plays: <span className="font-num text-emerald-300">{record.win}-{record.loss}-{record.push}</span>
            <span className={`font-num ml-2 ${record.units >= 0 ? "text-[#E5C158]" : "text-red-400"}`}>
              {record.units >= 0 ? "+" : ""}{record.units}u
            </span>
          </p>
        )}
      </div>
      {list.length === 0 ? (
        <p className="text-sm text-emerald-100/50" data-testid="no-edges">No plays above {Math.round(minEv * 100)}% EV.</p>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-2 snap-x">
          {list.map((e, i) => (
            <button key={`${e.game_id}-${e.market}-${e.side}`} onClick={() => onOpen(e.game_id)}
              data-testid={`top-edge-${i}`} style={{ animationDelay: `${i * 60}ms` }}
              className="rise snap-start shrink-0 w-60 text-left rounded-lg bg-[#0A2216] border border-[#D4AF37]/20 p-4 hover:-translate-y-0.5 hover:border-[#D4AF37]/70 transition-[transform,border-color] duration-200">
              <div className="flex justify-between text-[11px] uppercase tracking-widest text-emerald-400/80">
                <span>{e.market_label}</span><span>{e.matchup}</span>
              </div>
              <div className="mt-3 font-display text-lg font-semibold">{betLabel(e)}</div>
              <div className="mt-1 flex items-center justify-between text-sm">
                <span className="text-emerald-100/60">{e.book_title} <span className="font-num text-emerald-50">{fmtPrice(e.price)}</span></span>
                <span className="font-num font-bold text-[#E5C158]">{fmtEv(e.ev)}</span>
              </div>
              <div className="mt-2 flex justify-between text-xs text-emerald-100/50">
                <span>Model {fmtPct(e.model_prob)} vs {fmtPct(e.implied_prob)}</span>
                {e.result && <span className={`uppercase font-semibold ${RESULT[e.result]}`}>{e.result}</span>}
              </div>
            </button>
          ))}
        </div>
      )}
    </section>
  );
};
