import { Activity, BriefcaseBusiness } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getBusinessStats, type BusinessStats } from "@/lib/api";
import { DashboardPage } from "@/pages/dashboard-page";
import { LeadManagementPage } from "@/pages/lead-management-page";

export default function App() {
  const [activePage, setActivePage] = useState<"dashboard" | "leads">("dashboard");
  const [stats, setStats] = useState<BusinessStats | null>(null);

  async function loadStats(): Promise<void> {
    try {
      setStats(await getBusinessStats());
    } catch {
      setStats(null);
    }
  }

  useEffect(() => {
    let isCurrent = true;

    getBusinessStats()
      .then((businessStats) => {
        if (isCurrent) {
          setStats(businessStats);
        }
      })
      .catch(() => {
        if (isCurrent) {
          setStats(null);
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
          </div>
        </div>
      </section>

      {activePage === "dashboard" ? (
        <DashboardPage stats={stats} onStatsRefresh={() => void loadStats()} />
      ) : (
        <LeadManagementPage onStatsChanged={() => void loadStats()} />
      )}
    </main>
  );
}
