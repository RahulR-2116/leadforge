import { Activity, BriefcaseBusiness, CalendarClock, Mail, RefreshCw, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getHealthCheck, type HealthCheck } from "@/lib/api";

type DashboardMetric = {
  label: string;
  value: string;
  detail: string;
  icon: typeof BriefcaseBusiness;
};

export function DashboardPage() {
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const metrics = useMemo<DashboardMetric[]>(
    () => [
      {
        label: "Businesses",
        value: "0",
        detail: "Ready for imported leads",
        icon: BriefcaseBusiness,
      },
      { label: "Messages", value: "0", detail: "Outreach pipeline initialized", icon: Mail },
      { label: "Follow-ups", value: "0", detail: "No pending actions yet", icon: CalendarClock },
      { label: "Users", value: "0", detail: "Authentication phase pending", icon: Users },
    ],
    [],
  );

  async function loadHealthCheck(): Promise<void> {
    setIsLoading(true);
    setError(null);

    try {
      setHealth(await getHealthCheck());
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Unable to reach API";
      setError(message);
      setHealth(null);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let isCurrent = true;

    getHealthCheck()
      .then((healthCheck) => {
        if (isCurrent) {
          setHealth(healthCheck);
        }
      })
      .catch((caughtError: unknown) => {
        if (!isCurrent) {
          return;
        }

        const message = caughtError instanceof Error ? caughtError.message : "Unable to reach API";
        setError(message);
        setHealth(null);
      })
      .finally(() => {
        if (isCurrent) {
          setIsLoading(false);
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
          <div>
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
          </div>

          <div className="flex items-center gap-3">
            <Badge variant={health?.status === "ok" ? "secondary" : "outline"}>
              API {health?.status ?? "checking"}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void loadHealthCheck()}
              disabled={isLoading}
            >
              <RefreshCw
                className={isLoading ? "h-4 w-4 animate-spin" : "h-4 w-4"}
                aria-hidden="true"
              />
              Refresh
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-7xl px-5 py-8 lg:px-8">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => {
            const Icon = metric.icon;

            return (
              <Card key={metric.label}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                  <CardTitle>{metric.label}</CardTitle>
                  <Icon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-semibold">{metric.value}</div>
                  <p className="mt-1 text-sm text-muted-foreground">{metric.detail}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-[1.4fr_0.6fr]">
          <Card>
            <CardHeader>
              <CardTitle>Pipeline Overview</CardTitle>
              <CardDescription>
                CRM modules are wired and ready for Phase 2 features.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-3">
                {["Lead discovery", "Outreach", "Demo tracking"].map((stage) => (
                  <div key={stage} className="rounded-md border bg-background p-4">
                    <p className="text-sm font-medium">{stage}</p>
                    <p className="mt-2 text-2xl font-semibold">0</p>
                    <p className="mt-1 text-xs text-muted-foreground">Awaiting records</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>Live status from the FastAPI health endpoint.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <StatusRow label="Service" value={health?.service ?? "LeadForge"} />
              <StatusRow label="Environment" value={health?.environment ?? "development"} />
              <StatusRow label="Database" value={health?.database ?? "checking"} />
              {error ? (
                <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-destructive">
                  {error}
                </p>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border bg-background px-3 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
