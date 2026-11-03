import axios from "axios";

export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const getMeta = () => axios.get(`${API}/nfl/meta`).then((r) => r.data);
export const getWeek = (season, week) =>
  axios.get(`${API}/nfl/week`, { params: { season, week } }).then((r) => r.data);
export const refreshOdds = (season, week) =>
  axios.post(`${API}/nfl/odds/refresh`, null, { params: { season, week } }).then((r) => r.data);
export const runPipeline = (season, week) =>
  axios.post(`${API}/nfl/pipeline/run`, null, { params: { season, week } }).then((r) => r.data);
export const pipelineStatus = () => axios.get(`${API}/nfl/pipeline/status`).then((r) => r.data);

export const fmtPrice = (p) => (p == null ? "—" : p > 0 ? `+${p}` : `${p}`);
export const fmtPoint = (p) => (p == null ? "" : p > 0 ? `+${p}` : `${p}`);
export const fmtEv = (ev) => `${ev >= 0 ? "+" : ""}${(ev * 100).toFixed(1)}%`;
export const fmtPct = (p) => `${(p * 100).toFixed(0)}%`;

export const kickoff = (day, time) => {
  const d = new Date(`${day}T12:00:00`);
  const wd = d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  if (!time) return wd;
  const [h, m] = time.split(":").map(Number);
  return `${wd} · ${((h + 11) % 12) + 1}:${String(m).padStart(2, "0")} ${h >= 12 ? "PM" : "AM"} ET`;
};

export const betLabel = (e) => {
  if (e.market.endsWith("_ml")) return `${e.team} ML`;
  if (e.market.endsWith("_spread")) return `${e.team} ${fmtPoint(e.point)}`;
  return `${e.side === "over" ? "Over" : "Under"} ${e.point}`;
};

export const evClass = (ev) =>
  ev >= 0.04 ? "text-[#ffb71b]" : ev > 0 ? "text-teal-300" : "text-[#718789]";
