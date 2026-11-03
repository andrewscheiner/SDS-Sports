import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fmtEv, fmtPoint, fmtPrice, fmtPct, evClass } from "@/lib/nfl";

const Cell = ({ edge, point }) =>
  !edge ? <span className="text-[#718789]">—</span> : (
    <div className="font-num leading-tight">
      <div>{point != null && <span className="text-[#a9b9ba] mr-1">{point}</span>}{fmtPrice(edge.price)}</div>
      <div className={`text-[11px] ${evClass(edge.ev)}`}>{fmtEv(edge.ev)}</div>
    </div>
  );

export const OddsDialog = ({ game: g, onClose }) => {
  const [p, setP] = useState("q1");
  if (!g) return null;
  const find = (book, market, side) => g.edges.find((e) => e.book === book && e.market === `${p}_${market}` && e.side === side);
  const f = g.fair[p];
  const cols = [
    ["ml", "away", `${g.away_team} ML`], ["ml", "home", `${g.home_team} ML`],
    ["spread", "away", `${g.away_team} spr`], ["spread", "home", `${g.home_team} spr`],
    ["total", "over", "Over"], ["total", "under", "Under"],
  ];
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent data-testid="odds-dialog" className="max-w-4xl bg-[#10282b] border-[#ffb71b]/30 text-[#ffffff]">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl">{g.away_team} @ {g.home_team}</DialogTitle>
          <DialogDescription className="text-[#a9b9ba]">
            {g.odds_source === "live" ? "Live odds" : "Sample odds"} · EV uses model win probability with pushes on ties.
          </DialogDescription>
        </DialogHeader>
        <Tabs value={p} onValueChange={setP}>
          <TabsList className="bg-[#071719] border border-[#ffb71b]/20">
            <TabsTrigger value="q1" data-testid="dialog-tab-q1" className="data-[state=active]:bg-[#ffb71b] data-[state=active]:text-[#071719]">1st Quarter</TabsTrigger>
            <TabsTrigger value="h1" data-testid="dialog-tab-h1" className="data-[state=active]:bg-[#ffb71b] data-[state=active]:text-[#071719]">1st Half</TabsTrigger>
          </TabsList>
        </Tabs>
        <div data-testid="model-fair-line" className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          {[["Projected", `${g.away_team} ${f.away.toFixed(1)} – ${f.home.toFixed(1)} ${g.home_team}`],
            ["Win / tie", `${fmtPct(f.p_away)} / ${fmtPct(f.p_tie)} / ${fmtPct(f.p_home)}`],
            ["Fair ML", `${fmtPrice(f.fair_ml_away)} / ${fmtPrice(f.fair_ml_home)}`],
            ["Fair spread · total", `${g.home_team} ${fmtPoint(-f.margin.toFixed(1))} · ${f.total.toFixed(1)}`]].map(([k, v]) => (
            <div key={k} className="rounded-md bg-[#071719] border border-white/10 p-3">
              <div className="text-[10px] uppercase tracking-widest text-[#718789]">{k}</div>
              <div className="font-num mt-1 text-[#ffb71b]">{v}</div>
            </div>
          ))}
        </div>
        <div className="overflow-x-auto">
          <Table data-testid="odds-table">
            <TableHeader>
              <TableRow className="border-white/10 hover:bg-transparent">
                <TableHead className="text-[#718789]">Book</TableHead>
                {cols.map(([, , l]) => <TableHead key={l} className="text-[#718789] text-right whitespace-nowrap">{l}</TableHead>)}
              </TableRow>
            </TableHeader>
            <TableBody>
              {g.books.map((b) => (
                <TableRow key={b.book} data-testid={`odds-row-${b.book}`} className="border-white/10 hover:bg-white/5">
                  <TableCell className="font-semibold whitespace-nowrap">{b.title}</TableCell>
                  {cols.map(([m, s, l]) => {
                    const e = find(b.book, m, s);
                    const pt = m === "spread" ? fmtPoint(e?.point) : m === "total" ? e?.point : null;
                    return <TableCell key={l} className="text-right"><Cell edge={e} point={pt} /></TableCell>;
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </DialogContent>
    </Dialog>
  );
};
