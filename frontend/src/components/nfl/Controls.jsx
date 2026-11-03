import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { RefreshCw, Cpu } from "lucide-react";

export const Controls = ({ meta, week, setWeek, period, setPeriod, minEv, setMinEv, busy, onRefreshOdds, onRetrain }) => (
  <section data-testid="control-bar" className="pt-8 flex flex-col lg:flex-row lg:items-center gap-5 lg:gap-8">
    <Select value={String(week)} onValueChange={(v) => setWeek(Number(v))}>
      <SelectTrigger data-testid="week-select" className="w-56 bg-[#10282b] border-[#ffb71b]/25 font-display">
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="bg-[#10282b] border-[#ffb71b]/25">
        {meta.weeks.map((w) => (
          <SelectItem key={w} value={String(w)} data-testid={`week-option-${w}`}>
            {meta.season} Week {w}{w === meta.current_week ? " · current" : ""}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>

    <Tabs value={period} onValueChange={setPeriod}>
      <TabsList className="bg-[#10282b] border border-[#ffb71b]/20">
        {[["all", "All"], ["q1", "1st Quarter"], ["h1", "1st Half"]].map(([v, l]) => (
          <TabsTrigger key={v} value={v} data-testid={`period-tab-${v}`}
            className="data-[state=active]:bg-[#ffb71b] data-[state=active]:text-[#071719]">
            {l}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>

    <div className="flex items-center gap-3 w-full lg:w-60">
      <span className="text-xs uppercase tracking-widest text-[#718789] whitespace-nowrap">Min EV</span>
      <Slider data-testid="min-ev-slider" value={[minEv * 100]} min={0} max={15} step={1}
        onValueChange={([v]) => setMinEv(v / 100)} />
      <span className="font-num text-sm text-[#ffb71b] w-10" data-testid="min-ev-value">{Math.round(minEv * 100)}%</span>
    </div>

    <div className="flex gap-2 lg:ml-auto">
      <Button data-testid="refresh-odds-btn" variant="outline" disabled={busy} onClick={onRefreshOdds}
        className="border-[#ffb71b]/40 bg-transparent text-[#ffb71b] hover:bg-[#ffb71b]/10 hover:text-[#ffc33d]">
        <RefreshCw className="h-4 w-4 mr-2" /> Odds
      </Button>
      <Button data-testid="retrain-btn" disabled={busy} onClick={onRetrain}
        className="bg-[#ffb71b] text-[#071719] hover:bg-[#ffc33d]">
        <Cpu className="h-4 w-4 mr-2" /> Retrain
      </Button>
    </div>
  </section>
);
