import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { RefreshCw, Cpu } from "lucide-react";

export const Controls = ({ meta, week, setWeek, period, setPeriod, minEv, setMinEv, busy, onRefreshOdds, onRetrain }) => (
  <section data-testid="control-bar" className="pt-8 flex flex-col lg:flex-row lg:items-center gap-5 lg:gap-8">
    <Select value={String(week)} onValueChange={(v) => setWeek(Number(v))}>
      <SelectTrigger data-testid="week-select" className="w-44 bg-[#0A2216] border-[#D4AF37]/25 font-display">
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="bg-[#0A2216] border-[#D4AF37]/25">
        {meta.weeks.map((w) => (
          <SelectItem key={w} value={String(w)} data-testid={`week-option-${w}`}>
            {meta.season} Week {w}{w === meta.current_week ? " · current" : ""}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>

    <Tabs value={period} onValueChange={setPeriod}>
      <TabsList className="bg-[#0A2216] border border-[#D4AF37]/20">
        {[["all", "All"], ["q1", "1st Quarter"], ["h1", "1st Half"]].map(([v, l]) => (
          <TabsTrigger key={v} value={v} data-testid={`period-tab-${v}`}
            className="data-[state=active]:bg-[#E5C158] data-[state=active]:text-[#04120B]">
            {l}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>

    <div className="flex items-center gap-3 w-full lg:w-60">
      <span className="text-xs uppercase tracking-widest text-emerald-400/80 whitespace-nowrap">Min EV</span>
      <Slider data-testid="min-ev-slider" value={[minEv * 100]} min={0} max={15} step={1}
        onValueChange={([v]) => setMinEv(v / 100)} />
      <span className="font-num text-sm text-[#E5C158] w-10" data-testid="min-ev-value">{Math.round(minEv * 100)}%</span>
    </div>

    <div className="flex gap-2 lg:ml-auto">
      <Button data-testid="refresh-odds-btn" variant="outline" disabled={busy} onClick={onRefreshOdds}
        className="border-[#D4AF37]/40 bg-transparent text-[#E5C158] hover:bg-[#E5C158]/10 hover:text-[#F5D061]">
        <RefreshCw className="h-4 w-4 mr-2" /> Odds
      </Button>
      <Button data-testid="retrain-btn" disabled={busy} onClick={onRetrain}
        className="bg-[#E5C158] text-[#04120B] hover:bg-[#F5D061]">
        <Cpu className="h-4 w-4 mr-2" /> Retrain
      </Button>
    </div>
  </section>
);
