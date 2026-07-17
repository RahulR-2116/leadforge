import { Activity, Bot, BriefcaseBusiness, MapPinned } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  getBusinessStats,
  getLatestScrapeJob,
  type BusinessStats,
  type ScrapeJob,
} from "@/lib/api";
import { AIAssistantPage } from "@/pages/ai-assistant-page";
import { DashboardPage } from "@/pages/dashboard-page";
import { LeadManagementPage } from "@/pages/lead-management-page";
import { ScraperPage } from "@/pages/scraper-page";

export default function App() {
  const [activePage, setActivePage] = useState<"dashboard" | "leads" | "scraper" | "ai">(
    "dashboard",
  );
  const [stats, setStats] = useState<BusinessStats | null>(null);
  const [latestScrapeJob, setLatestScrapeJob] = useState<ScrapeJob | null>(null);

  async function loadStats(): Promise<void> {
    try {
      setStats(await getBusinessStats());
    } catch {
      setStats(null);
    }
  }

  async function loadLatestScrapeJob(): Promise<void> {
    try {
      setLatestScrapeJob(await getLatestScrapeJob());
    } catch {
      setLatestScrapeJob(null);
    }
  }

  useEffect(() => {
    let isCurrent = true;

    Promise.all([getBusinessStats(), getLatestScrapeJob()])
      .then(([businessStats, scrapeJob]) => {
        if (isCurrent) {
          setStats(businessStats);
          setLatestScrapeJob(scrapeJob);
        }
      })
      .catch(() => {
        if (isCurrent) {
          setStats(null);
          setLatestScrapeJob(null);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  return (
    <main className="min-h-screen">
      <section className="border-b bg-card">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Activity className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-normal">LeadForge</h1>
              <p className="text-sm text-muted-foreground">
                Internal CRM and lead generation dashboard
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant={activePage === "dashboard" ? "default" : "outline"}
              size="sm"
              onClick={() => setActivePage("dashboard")}
            >
              Dashboard
            </Button>
            <Button
              variant={activePage === "leads" ? "default" : "outline"}
              size="sm"
              onClick={() => setActivePage("leads")}
            >
              <BriefcaseBusiness className="h-4 w-4" aria-hidden="true" />
              Leads
            </Button>
            <Button
              variant={activePage === "scraper" ? "default" : "outline"}
              size="sm"
              onClick={() => setActivePage("scraper")}
            >
              <MapPinned className="h-4 w-4" aria-hidden="true" />
              Scraper
            </Button>
            <Button
              variant={activePage === "ai" ? "default" : "outline"}
              size="sm"
              onClick={() => setActivePage("ai")}
            >
              <Bot className="h-4 w-4" aria-hidden="true" />
              AI
            </Button>
          </div>
        </div>
      </section>

      {activePage === "dashboard" ? (
        <DashboardPage
          stats={stats}
          latestScrapeJob={latestScrapeJob}
          onStatsRefresh={() => {
            void loadStats();
            void loadLatestScrapeJob();
          }}
        />
      ) : activePage === "leads" ? (
        <LeadManagementPage onStatsChanged={() => void loadStats()} />
      ) : activePage === "scraper" ? (
        <ScraperPage
          latestJob={latestScrapeJob}
          onJobChanged={setLatestScrapeJob}
          onBusinessesImported={() => void loadStats()}
        />
      ) : (
        <AIAssistantPage />
      )}
    </main>
  );
}
