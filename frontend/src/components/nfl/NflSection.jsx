import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { getMeta, getWeek, refreshOdds, runPipeline, pipelineStatus } from "@/lib/nfl";
import { DashHeader } from "@/components/nfl/DashHeader";
import { Controls } from "@/components/nfl/Controls";
import { TopEdges } from "@/components/nfl/TopEdges";
import { GameCard } from "@/components/nfl/GameCard";
import { OddsDialog } from "@/components/nfl/OddsDialog";
import { ModelPanel } from "@/components/nfl/ModelPanel";
import { SeasonTracker } from "@/components/nfl/SeasonTracker";

/** Drop-in section: <NflSection /> renders the whole NFL dashboard (needs Tailwind + react-query). */
export const NflSection = () => {
  const qc = useQueryClient();
  const meta = useQuery({ queryKey: ["meta"], queryFn: getMeta });
  const [week, setWeek] = useState(null);
  const [period, setPeriod] = useState("all");
  const [minEv, setMinEv] = useState(0.02);
  const [open, setOpen] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (meta.data && week == null) setWeek(meta.data.current_week);
  }, [meta.data, week]);

  const season = meta.data?.season;
  const wk = useQuery({
    queryKey: ["week", season, week],
    queryFn: () => getWeek(season, week),
    enabled: !!season && !!week,
  });

  const onRefreshOdds = async () => {
    setBusy(true);
    try {
      const r = await refreshOdds(season, week);
      toast.success(r.key_configured ? `Odds updated (${r.live} live games)` : "No Odds API key yet — sample odds regenerated");
      qc.invalidateQueries({ queryKey: ["week"] });
    } catch (e) {
      toast.error(e.response?.data?.detail || "Odds refresh failed");
    }
    setBusy(false);
  };

  const onRetrain = async () => {
    setBusy(true);
    try {
      await runPipeline(season);
      toast.message("Retraining on latest nflverse data…");
      const poll = setInterval(async () => {
        const s = await pipelineStatus();
        if (s.status === "running") return;
        clearInterval(poll);
        setBusy(false);
        s.status === "done" ? toast.success(`Model retrained: ${s.message}`) : toast.error(s.message);
        qc.invalidateQueries();
      }, 3000);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Could not start retrain");
      setBusy(false);
    }
  };

  const games = wk.data?.games || [];
  const openGame = games.find((g) => g.game_id === open);

  return (
    <section id="sports" data-testid="nfl-dashboard">
      <DashHeader meta={meta.data} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 space-y-10">
        {meta.isError && (
          <p className="text-red-400" data-testid="meta-error">Model not trained yet. Run the pipeline from the backend.</p>
        )}
        {meta.data && week && (
          <Controls
            meta={meta.data} week={week} setWeek={setWeek} period={period} setPeriod={setPeriod}
            minEv={minEv} setMinEv={setMinEv} busy={busy} onRefreshOdds={onRefreshOdds} onRetrain={onRetrain}
          />
        )}
        {wk.data && (
          <TopEdges edges={wk.data.top_edges} record={wk.data.record} period={period} minEv={minEv} onOpen={setOpen} />
        )}
        <section data-testid="games-grid" className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {wk.isLoading && <p className="text-[#a9b9ba]">Loading games…</p>}
          {games.map((g, i) => (
            <GameCard key={g.game_id} game={g} index={i} period={period} minEv={minEv} onOpen={() => setOpen(g.game_id)} />
          ))}
        </section>
        {meta.data && <SeasonTracker season={meta.data.season} />}
        {meta.data && <ModelPanel meta={meta.data} />}
      </main>
      <OddsDialog game={openGame} onClose={() => setOpen(null)} />
    </section>
  );
};
