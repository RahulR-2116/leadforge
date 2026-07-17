import { CheckCircle2, Loader2, MapPinned, Play, TriangleAlert } from "lucide-react";
import { type FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getScrapeJob,
  startGoogleMapsScrape,
  type GoogleMapsScrapePayload,
  type ScrapeJob,
} from "@/lib/api";
import { cn } from "@/lib/utils";

type ScraperPageProps = {
  latestJob: ScrapeJob | null;
  onJobChanged: (job: ScrapeJob | null) => void;
  onBusinessesImported: () => void;
};

export function ScraperPage({ latestJob, onJobChanged, onBusinessesImported }: ScraperPageProps) {
  const [form, setForm] = useState<GoogleMapsScrapePayload>({
    category: "Salon",
    city: "Hyderabad",
    maximum_results: 100,
  });
  const [job, setJob] = useState<ScrapeJob | null>(latestJob);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const activeJob = job ?? latestJob;
  const isRunning = activeJob?.status === "QUEUED" || activeJob?.status === "RUNNING";
  const statusTone = useMemo(() => {
    if (activeJob?.status === "COMPLETED") {
      return "border-emerald-200 bg-emerald-50 text-emerald-800";
    }
    if (activeJob?.status === "FAILED") {
      return "border-destructive/30 bg-destructive/10 text-destructive";
    }
    return "border-sky-200 bg-sky-50 text-sky-800";
  }, [activeJob?.status]);

  useEffect(() => {
    if (!activeJob || !isRunning) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void getScrapeJob(activeJob.job_id)
        .then((updatedJob) => {
          setJob(updatedJob);
          onJobChanged(updatedJob);
          if (updatedJob.status === "COMPLETED") {
            onBusinessesImported();
          }
        })
        .catch((caughtError: unknown) => {
          setError(getErrorMessage(caughtError));
        });
    }, 2000);

    return () => window.clearInterval(intervalId);
  }, [activeJob, isRunning, onBusinessesImported, onJobChanged]);

  async function handleStart(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setIsStarting(true);
    setError(null);

    try {
      const startedJob = await startGoogleMapsScrape(form);
      setJob(startedJob);
      onJobChanged(startedJob);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsStarting(false);
    }
  }

  return (
    <section className="mx-auto w-full max-w-7xl px-5 py-8 lg:px-8">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold tracking-normal">Lead Collection Engine</h2>
        <p className="text-sm text-muted-foreground">
          Import Google Maps businesses directly into the CRM with deduplication.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[0.75fr_1.25fr]">
        <Card>
          <CardHeader>
            <CardTitle>Google Maps Search</CardTitle>
            <CardDescription>
              Choose a category and city, then start a background scrape.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={(event) => void handleStart(event)}>
              <TextInput
                label="Category"
                value={form.category}
                onChange={(value) => setForm((current) => ({ ...current, category: value }))}
              />
              <TextInput
                label="City"
                value={form.city}
                onChange={(value) => setForm((current) => ({ ...current, city: value }))}
              />
              <label className="grid gap-1 text-sm font-medium">
                Maximum Results
                <input
                  className="h-9 rounded-md border bg-background px-3 text-sm font-normal outline-none focus:ring-2 focus:ring-ring"
                  type="number"
                  min={1}
                  max={500}
                  value={form.maximum_results}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      maximum_results: Number(event.target.value),
                    }))
                  }
                />
              </label>
              <Button type="submit" disabled={isStarting || isRunning}>
                {isStarting ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Play className="h-4 w-4" aria-hidden="true" />
                )}
                Start Scraping
              </Button>
            </form>
            {error ? (
              <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Live Progress</CardTitle>
              <CardDescription>
                Current task, processed businesses, ETA, imports, duplicates, and errors.
              </CardDescription>
            </div>
            {activeJob ? (
              <Badge className={cn("border", statusTone)}>{activeJob.status}</Badge>
            ) : null}
          </CardHeader>
          <CardContent>
            {activeJob ? (
              <div className="space-y-5">
                <div>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-medium">{activeJob.current_task}</span>
                    <span className="text-muted-foreground">{Math.round(activeJob.progress)}%</span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-md bg-muted">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${Math.min(activeJob.progress, 100)}%` }}
                    />
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-3">
                  <Metric label="Found" value={activeJob.businesses_found} />
                  <Metric label="Imported" value={activeJob.businesses_imported} />
                  <Metric label="Duplicates" value={activeJob.duplicates_skipped} />
                  <Metric label="Processed" value={activeJob.businesses_processed} />
                  <Metric label="Errors" value={activeJob.errors.length} />
                  <Metric label="ETA" value={formatEta(activeJob.eta_seconds)} />
                </div>

                <div className="rounded-md border bg-background p-4 text-sm">
                  <div className="mb-2 flex items-center gap-2 font-medium">
                    <MapPinned className="h-4 w-4 text-primary" aria-hidden="true" />
                    Current business
                  </div>
                  <p className="text-muted-foreground">
                    {activeJob.current_business ?? "Waiting for results"}
                  </p>
                </div>

                {activeJob.status === "COMPLETED" ? (
                  <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
                    <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                    Scrape complete. Imported businesses are now available in the CRM.
                  </div>
                ) : null}

                {activeJob.errors.length ? (
                  <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                    <div className="mb-2 flex items-center gap-2 font-medium">
                      <TriangleAlert className="h-4 w-4" aria-hidden="true" />
                      Recent errors
                    </div>
                    <ul className="space-y-1">
                      {activeJob.errors.map((jobError) => (
                        <li key={jobError}>{jobError}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="rounded-md border bg-background p-6 text-sm text-muted-foreground">
                No scraping task has been started yet.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function TextInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1 text-sm font-medium">
      {label}
      <input
        className="h-9 rounded-md border bg-background px-3 text-sm font-normal outline-none focus:ring-2 focus:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required
      />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border bg-background p-4">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function formatEta(seconds: number | null): string {
  if (seconds === null) {
    return "Calculating";
  }
  if (seconds < 60) {
    return `${seconds}s`;
  }
  return `${Math.ceil(seconds / 60)}m`;
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong";
}
