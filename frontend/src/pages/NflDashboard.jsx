import { SiteHeader, SiteFooter } from "@/components/site/SiteChrome";
import { NflSection } from "@/components/nfl/NflSection";

export default function NflDashboard() {
  return (
    <div className="app-container">
      <SiteHeader />
      <NflSection />
      <SiteFooter />
    </div>
  );
}
