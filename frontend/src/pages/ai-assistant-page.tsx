import { Bot, FileText, Globe, Loader2, Mail, MessageCircle, Play, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  generateAudit,
  generateConversationReply,
  generateEmail,
  generateFollowUp,
  generateObjectionReplies,
  generateProposal,
  generateSummary,
  generateWhatsapp,
  getDemoJob,
  getDemoTemplates,
  getPrompts,
  listBusinesses,
  startDemoGeneration,
  updatePrompt,
  type Business,
  type DemoJob,
} from "@/lib/api";

type HistoryItem = {
  title: string;
  content: string;
};

export function AIAssistantPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [prompts, setPrompts] = useState<Record<string, string>>({});
  const [promptKey, setPromptKey] = useState("whatsapp");
  const [promptDraft, setPromptDraft] = useState("");
  const [templates, setTemplates] = useState<string[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("salon");
  const [conversationMessage, setConversationMessage] = useState("");
  const [objection, setObjection] = useState("");
  const [demoJob, setDemoJob] = useState<DemoJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;
    Promise.all([
      listBusinesses({ page: 1, page_size: 100, sort_by: "updated_at", sort_direction: "desc" }),
      getPrompts(),
      getDemoTemplates(),
    ])
      .then(([businessResponse, promptResponse, templateResponse]) => {
        if (!isCurrent) {
          return;
        }
        setBusinesses(businessResponse.items);
        setBusinessId(businessResponse.items[0]?.id ?? null);
        setPrompts(promptResponse);
        setPromptKey(Object.keys(promptResponse)[0] ?? "whatsapp");
        setPromptDraft(Object.values(promptResponse)[0] ?? "");
        setTemplates(templateResponse);
        setSelectedTemplate(templateResponse[0] ?? "salon");
      })
      .catch((caughtError: unknown) => setError(getErrorMessage(caughtError)));
    return () => {
      isCurrent = false;
    };
  }, []);

  useEffect(() => {
    if (!demoJob || demoJob.status === "COMPLETED" || demoJob.status === "FAILED") {
      return;
    }
    const intervalId = window.setInterval(() => {
      void getDemoJob(demoJob.job_id)
        .then(setDemoJob)
        .catch((caughtError: unknown) => setError(getErrorMessage(caughtError)));
    }, 2000);
    return () => window.clearInterval(intervalId);
  }, [demoJob]);

  async function runAction(
    title: string,
    action: () => Promise<{ content: string }>,
  ): Promise<void> {
    if (!businessId) {
      setError("Select a business first");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await action();
      setHistory((current) => [{ title, content: response.content }, ...current]);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleEmail(): Promise<void> {
    if (!businessId) {
      return;
    }
    setIsLoading(true);
    try {
      const response = await generateEmail(businessId);
      setHistory((current) => [
        {
          title: "Cold Email",
          content: `Subject: ${response.subject}\n\n${response.email}\n\nCTA: ${response.cta}`,
        },
        ...current,
      ]);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleAudit(): Promise<void> {
    if (!businessId) {
      return;
    }
    setIsLoading(true);
    try {
      const response = await generateAudit(businessId);
      setHistory((current) => [
        { title: "Website Audit", content: `Score: ${response.score}/100\n\n${response.content}` },
        ...current,
      ]);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsLoading(false);
    }
  }

  async function handlePromptSave(): Promise<void> {
    const updated = await updatePrompt(promptKey, promptDraft);
    setPrompts(updated);
  }

  async function handleDemoStart(): Promise<void> {
    if (!businessId) {
      return;
    }
    setDemoJob(await startDemoGeneration(businessId, selectedTemplate));
  }

  return (
    <section className="mx-auto w-full max-w-7xl px-5 py-8 lg:px-8">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold tracking-normal">AI Sales Assistant</h2>
        <p className="text-sm text-muted-foreground">
          Generate outreach, audits, proposals, summaries, replies, and personalized demo websites.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.75fr_1.25fr]">
        <Card>
          <CardHeader>
            <CardTitle>Controls</CardTitle>
            <CardDescription>Select a lead and run a sales action.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <select
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              value={businessId ?? ""}
              onChange={(event) => setBusinessId(Number(event.target.value))}
            >
              {businesses.map((business) => (
                <option key={business.id} value={business.id}>
                  {business.business_name}
                </option>
              ))}
            </select>

            <div className="grid gap-2 md:grid-cols-2">
              <ActionButton
                icon={<MessageCircle />}
                label="WhatsApp"
                onClick={() => runAction("WhatsApp", () => generateWhatsapp(businessId!))}
              />
              <ActionButton icon={<Mail />} label="Email" onClick={() => void handleEmail()} />
              <ActionButton
                icon={<Sparkles />}
                label="Follow-up"
                onClick={() =>
                  runAction("Follow-up", () => generateFollowUp(businessId!, "No reply"))
                }
              />
              <ActionButton icon={<Globe />} label="Audit" onClick={() => void handleAudit()} />
              <ActionButton
                icon={<FileText />}
                label="Proposal"
                onClick={() => runAction("Proposal", () => generateProposal(businessId!))}
              />
              <ActionButton
                icon={<Bot />}
                label="Summary"
                onClick={() => runAction("Summary", () => generateSummary(businessId!))}
              />
            </div>

            <div className="space-y-2">
              <input
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                placeholder="Customer objection"
                value={objection}
                onChange={(event) => setObjection(event.target.value)}
              />
              <Button
                className="w-full"
                variant="outline"
                onClick={() =>
                  runAction("Objection Replies", () => generateObjectionReplies(objection))
                }
              >
                Generate Objection Replies
              </Button>
            </div>

            <div className="space-y-2">
              <input
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                placeholder="Latest customer message"
                value={conversationMessage}
                onChange={(event) => setConversationMessage(event.target.value)}
              />
              <Button
                className="w-full"
                variant="outline"
                onClick={() =>
                  runAction("Conversation Reply", () =>
                    generateConversationReply(businessId!, conversationMessage),
                  )
                }
              >
                Continue Conversation
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Demo Website Generator</CardTitle>
              <CardDescription>
                Generate, build, deploy, and save a personalized demo site.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <select
                  className="h-10 rounded-md border bg-background px-3 text-sm"
                  value={selectedTemplate}
                  onChange={(event) => setSelectedTemplate(event.target.value)}
                >
                  {templates.map((template) => (
                    <option key={template} value={template}>
                      {template.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
                <Button onClick={() => void handleDemoStart()}>
                  <Play className="h-4 w-4" aria-hidden="true" />
                  Generate Demo Website
                </Button>
              </div>
              {demoJob ? (
                <div>
                  <div className="mb-2 flex justify-between text-sm">
                    <span>{demoJob.current_task}</span>
                    <span>{Math.round(demoJob.progress)}%</span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-md bg-muted">
                    <div className="h-full bg-primary" style={{ width: `${demoJob.progress}%` }} />
                  </div>
                  {demoJob.demo_url ? (
                    <a
                      className="mt-3 inline-block text-sm text-primary"
                      href={demoJob.demo_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open website preview
                    </a>
                  ) : null}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Prompt Library</CardTitle>
              <CardDescription>Edit reusable prompt templates.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <select
                className="h-10 rounded-md border bg-background px-3 text-sm"
                value={promptKey}
                onChange={(event) => {
                  setPromptKey(event.target.value);
                  setPromptDraft(prompts[event.target.value] ?? "");
                }}
              >
                {Object.keys(prompts).map((key) => (
                  <option key={key} value={key}>
                    {key}
                  </option>
                ))}
              </select>
              <textarea
                className="min-h-32 w-full rounded-md border bg-background p-3 text-sm"
                value={promptDraft}
                onChange={(event) => setPromptDraft(event.target.value)}
              />
              <Button variant="outline" onClick={() => void handlePromptSave()}>
                Save Prompt
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Generation History</CardTitle>
              <CardDescription>Recent AI outputs for the selected lead.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                <p className="text-sm text-muted-foreground">
                  <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                  Generating...
                </p>
              ) : null}
              {error ? (
                <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </p>
              ) : null}
              {history.map((item) => (
                <div
                  key={`${item.title}-${item.content.slice(0, 12)}`}
                  className="rounded-md border bg-background p-4"
                >
                  <p className="font-medium">{item.title}</p>
                  <pre className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                    {item.content}
                  </pre>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}

function ActionButton({
  icon,
  label,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <Button variant="outline" onClick={onClick}>
      <span className="[&>svg]:h-4 [&>svg]:w-4">{icon}</span>
      {label}
    </Button>
  );
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong";
}
