import {
  Download,
  ExternalLink,
  FileSpreadsheet,
  Loader2,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BUSINESS_STATUSES,
  addDemo,
  addFollowUp,
  addMessage,
  bulkDeleteBusinesses,
  bulkUpdateBusinessStatus,
  createBusiness,
  deleteBusiness,
  exportUrl,
  getBusiness,
  listBusinesses,
  updateBusiness,
  type Business,
  type BusinessDetail,
  type BusinessPayload,
  type BusinessStatus,
} from "@/lib/api";
import { cn } from "@/lib/utils";

type Toast = {
  type: "success" | "error";
  message: string;
};

type LeadManagementPageProps = {
  onStatsChanged: () => void;
};

const emptyForm: BusinessPayload = {
  business_name: "",
  category: "",
  phone_number: "",
  email: "",
  address: "",
  city: "",
  state: "",
  country: "India",
  website: "",
  has_website: false,
  google_maps_url: "",
  justdial_url: "",
  rating: null,
  review_count: null,
  status: "NEW",
  notes: "",
};

const statusClasses: Record<BusinessStatus, string> = {
  NEW: "border-slate-200 bg-slate-100 text-slate-700",
  CONTACTED: "border-sky-200 bg-sky-100 text-sky-800",
  REPLIED: "border-emerald-200 bg-emerald-100 text-emerald-800",
  DEMO_REQUESTED: "border-amber-200 bg-amber-100 text-amber-800",
  DEMO_SENT: "border-indigo-200 bg-indigo-100 text-indigo-800",
  NEGOTIATING: "border-fuchsia-200 bg-fuchsia-100 text-fuchsia-800",
  CLIENT: "border-green-200 bg-green-100 text-green-800",
  LOST: "border-rose-200 bg-rose-100 text-rose-800",
};

export function LeadManagementPage({ onStatsChanged }: LeadManagementPageProps) {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<BusinessDetail | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [form, setForm] = useState<BusinessPayload>(emptyForm);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({
    category: "",
    city: "",
    state: "",
    has_website: "",
    status: "" as BusinessStatus | "",
  });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [bulkStatus, setBulkStatus] = useState<BusinessStatus>("CONTACTED");
  const [notesDraft, setNotesDraft] = useState("");
  const [followUpDraft, setFollowUpDraft] = useState("");
  const [messageDraft, setMessageDraft] = useState("");
  const [demoDraft, setDemoDraft] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);

  const categoryOptions = useMemo(
    () => Array.from(new Set(businesses.map((business) => business.category).filter(Boolean))),
    [businesses],
  );
  const cityOptions = useMemo(
    () => Array.from(new Set(businesses.map((business) => business.city).filter(Boolean))),
    [businesses],
  );
  const stateOptions = useMemo(
    () => Array.from(new Set(businesses.map((business) => business.state).filter(Boolean))),
    [businesses],
  );

  async function loadBusinesses(nextPage = page): Promise<void> {
    setIsLoading(true);
    try {
      const response = await listBusinesses({
        page: nextPage,
        page_size: 10,
        search,
        category: filters.category,
        city: filters.city,
        state: filters.state,
        has_website: filters.has_website,
        status: filters.status,
        sort_by: "updated_at",
        sort_direction: "desc",
      });
      setBusinesses(response.items);
      setTotal(response.total);
      setPages(response.pages);
      setPage(response.page);
    } catch (error) {
      showToast("error", getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshDetail(id: number): Promise<void> {
    setSelectedBusiness(await getBusiness(id));
  }

  useEffect(() => {
    let isCurrent = true;

    listBusinesses({
      page: 1,
      page_size: 10,
      sort_by: "updated_at",
      sort_direction: "desc",
    })
      .then((response) => {
        if (!isCurrent) {
          return;
        }
        setBusinesses(response.items);
        setTotal(response.total);
        setPages(response.pages);
        setPage(response.page);
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          showToast("error", getErrorMessage(error));
        }
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

  function showToast(type: Toast["type"], message: string): void {
    setToast({ type, message });
    window.setTimeout(() => setToast(null), 4000);
  }

  function updateForm<K extends keyof BusinessPayload>(key: K, value: BusinessPayload[K]): void {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function cleanFormPayload(): BusinessPayload {
    return Object.fromEntries(
      Object.entries(form).map(([key, value]) => [key, value === "" ? null : value]),
    ) as BusinessPayload;
  }

  async function handleCreateBusiness(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setIsSaving(true);
    try {
      const created = await createBusiness(cleanFormPayload());
      setForm(emptyForm);
      setSelectedBusiness(created);
      showToast("success", "Business lead created");
      await loadBusinesses(1);
      onStatsChanged();
    } catch (error) {
      showToast("error", getErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteBusiness(id: number): Promise<void> {
    try {
      await deleteBusiness(id);
      setSelectedBusiness(null);
      setSelectedIds((current) => current.filter((selectedId) => selectedId !== id));
      showToast("success", "Business deleted");
      await loadBusinesses();
      onStatsChanged();
    } catch (error) {
      showToast("error", getErrorMessage(error));
    }
  }

  async function handleBulkDelete(): Promise<void> {
    if (selectedIds.length === 0) {
      return;
    }
    try {
      await bulkDeleteBusinesses(selectedIds);
      setSelectedIds([]);
      setSelectedBusiness(null);
      showToast("success", "Selected businesses deleted");
      await loadBusinesses();
      onStatsChanged();
    } catch (error) {
      showToast("error", getErrorMessage(error));
    }
  }

  async function handleBulkStatus(): Promise<void> {
    if (selectedIds.length === 0) {
      return;
    }
    try {
      await bulkUpdateBusinessStatus(selectedIds, bulkStatus);
      showToast("success", "Selected statuses updated");
      await loadBusinesses();
      if (selectedBusiness && selectedIds.includes(selectedBusiness.id)) {
        await refreshDetail(selectedBusiness.id);
      }
      onStatsChanged();
    } catch (error) {
      showToast("error", getErrorMessage(error));
    }
  }

  async function handleNotesSave(): Promise<void> {
    if (!selectedBusiness) {
      return;
    }
    try {
      const updated = await updateBusiness(selectedBusiness.id, { notes: notesDraft });
      setSelectedBusiness(updated);
      showToast("success", "Notes updated");
    } catch (error) {
      showToast("error", getErrorMessage(error));
    }
  }

  async function handleAddFollowUp(): Promise<void> {
    if (!selectedBusiness || !followUpDraft) {
      return;
    }
    try {
      await addFollowUp(selectedBusiness.id, {
        date: new Date(followUpDraft).toISOString(),
        completed: false,
        notes: "Scheduled follow-up",
      });
      await refreshDetail(selectedBusiness.id);
      setFollowUpDraft("");
      showToast("success", "Follow-up added");
    } catch (error) {
      showToast("error", getErrorMessage(error));
    }
  }

  async function handleAddDemo(): Promise<void> {
    if (!selectedBusiness || !demoDraft) {
      return;
    }
    try {
      await addDemo(selectedBusiness.id, { demo_url: demoDraft, notes: "Demo added from CRM" });
      await refreshDetail(selectedBusiness.id);
      setDemoDraft("");
      showToast("success", "Demo added");
    } catch (error) {
      showToast("error", getErrorMessage(error));
    }
  }

  async function handleAddMessage(): Promise<void> {
    if (!selectedBusiness || !messageDraft.trim()) {
      return;
    }
    try {
      await addMessage(selectedBusiness.id, {
        message: messageDraft.trim(),
        sent: true,
        sent_at: new Date().toISOString(),
      });
      await refreshDetail(selectedBusiness.id);
      setMessageDraft("");
      showToast("success", "Message added");
    } catch (error) {
      showToast("error", getErrorMessage(error));
    }
  }

  function toggleSelected(id: number): void {
    setSelectedIds((current) =>
      current.includes(id) ? current.filter((selectedId) => selectedId !== id) : [...current, id],
    );
  }

  function selectBusiness(business: Business): void {
    setNotesDraft(business.notes ?? "");
    void getBusiness(business.id)
      .then(setSelectedBusiness)
      .catch((error: unknown) => showToast("error", getErrorMessage(error)));
  }

  return (
    <section className="mx-auto w-full max-w-7xl px-5 py-8 lg:px-8">
      {toast ? (
        <div
          className={cn(
            "fixed right-5 top-5 z-20 rounded-md border px-4 py-3 text-sm shadow-sm",
            toast.type === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-800"
              : "border-destructive/30 bg-destructive/10 text-destructive",
          )}
        >
          {toast.message}
        </div>
      ) : null}

      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-normal">Lead Management</h2>
          <p className="text-sm text-muted-foreground">
            Manage prospects, outreach status, demos, notes, and follow-up history.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <a href={exportUrl("csv")}>
              <Download className="h-4 w-4" aria-hidden="true" />
              CSV
            </a>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href={exportUrl("xlsx")}>
              <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />
              Excel
            </a>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.7fr]">
        <Card>
          <CardHeader>
            <CardTitle>Add Business</CardTitle>
            <CardDescription>
              Phone and business name duplicates are rejected by the API.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3" onSubmit={(event) => void handleCreateBusiness(event)}>
              <TextInput
                label="Business"
                value={form.business_name}
                onChange={(value) => updateForm("business_name", value)}
                required
              />
              <div className="grid gap-3 md:grid-cols-2">
                <TextInput
                  label="Category"
                  value={form.category ?? ""}
                  onChange={(value) => updateForm("category", value)}
                />
                <TextInput
                  label="Phone"
                  value={form.phone_number ?? ""}
                  onChange={(value) => updateForm("phone_number", value)}
                />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <TextInput
                  label="City"
                  value={form.city ?? ""}
                  onChange={(value) => updateForm("city", value)}
                />
                <TextInput
                  label="State"
                  value={form.state ?? ""}
                  onChange={(value) => updateForm("state", value)}
                />
              </div>
              <TextInput
                label="Website"
                value={form.website ?? ""}
                onChange={(value) => updateForm("website", value)}
              />
              <TextArea
                label="Notes"
                value={form.notes ?? ""}
                onChange={(value) => updateForm("notes", value)}
              />
              <Button type="submit" disabled={isSaving}>
                {isSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Plus className="h-4 w-4" aria-hidden="true" />
                )}
                Add Lead
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Businesses</CardTitle>
            <CardDescription>{total} leads in the current CRM view.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 lg:grid-cols-[1.3fr_repeat(5,0.8fr)_auto]">
              <div className="relative">
                <Search
                  className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground"
                  aria-hidden="true"
                />
                <input
                  className="h-9 w-full rounded-md border bg-background pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Search name, phone, category, city, state"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
              <Select
                value={filters.category}
                onChange={(value) => setFilters((current) => ({ ...current, category: value }))}
              >
                <option value="">Category</option>
                {categoryOptions.map((category) => (
                  <option key={category ?? ""} value={category ?? ""}>
                    {category}
                  </option>
                ))}
              </Select>
              <Select
                value={filters.city}
                onChange={(value) => setFilters((current) => ({ ...current, city: value }))}
              >
                <option value="">City</option>
                {cityOptions.map((city) => (
                  <option key={city ?? ""} value={city ?? ""}>
                    {city}
                  </option>
                ))}
              </Select>
              <Select
                value={filters.state}
                onChange={(value) => setFilters((current) => ({ ...current, state: value }))}
              >
                <option value="">State</option>
                {stateOptions.map((state) => (
                  <option key={state ?? ""} value={state ?? ""}>
                    {state}
                  </option>
                ))}
              </Select>
              <Select
                value={filters.has_website}
                onChange={(value) => setFilters((current) => ({ ...current, has_website: value }))}
              >
                <option value="">Website</option>
                <option value="true">Has website</option>
                <option value="false">No website</option>
              </Select>
              <Select
                value={filters.status}
                onChange={(value) =>
                  setFilters((current) => ({ ...current, status: value as BusinessStatus | "" }))
                }
              >
                <option value="">Status</option>
                {BUSINESS_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {formatStatus(status)}
                  </option>
                ))}
              </Select>
              <Button variant="outline" size="sm" onClick={() => void loadBusinesses(1)}>
                Apply
              </Button>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Select
                value={bulkStatus}
                onChange={(value) => setBulkStatus(value as BusinessStatus)}
              >
                {BUSINESS_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {formatStatus(status)}
                  </option>
                ))}
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void handleBulkStatus()}
                disabled={!selectedIds.length}
              >
                Change Status
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void handleBulkDelete()}
                disabled={!selectedIds.length}
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" />
                Delete
              </Button>
              <span className="text-sm text-muted-foreground">{selectedIds.length} selected</span>
            </div>

            <div className="overflow-hidden rounded-md border">
              <table className="w-full table-fixed text-sm">
                <thead className="bg-muted text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="w-10 px-3 py-3"></th>
                    <th className="px-3 py-3">Business</th>
                    <th className="px-3 py-3">Category</th>
                    <th className="px-3 py-3">Phone</th>
                    <th className="px-3 py-3">Website</th>
                    <th className="px-3 py-3">Status</th>
                    <th className="w-24 px-3 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr>
                      <td colSpan={7} className="px-3 py-8 text-center text-muted-foreground">
                        Loading leads...
                      </td>
                    </tr>
                  ) : businesses.length ? (
                    businesses.map((business) => (
                      <tr key={business.id} className="border-t">
                        <td className="px-3 py-3">
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(business.id)}
                            onChange={() => toggleSelected(business.id)}
                          />
                        </td>
                        <td className="truncate px-3 py-3 font-medium">{business.business_name}</td>
                        <td className="truncate px-3 py-3">{business.category ?? "-"}</td>
                        <td className="truncate px-3 py-3">{business.phone_number ?? "-"}</td>
                        <td className="truncate px-3 py-3">
                          {business.website ? (
                            <a
                              className="inline-flex items-center gap-1 text-primary"
                              href={business.website}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Visit <ExternalLink className="h-3 w-3" aria-hidden="true" />
                            </a>
                          ) : (
                            "No"
                          )}
                        </td>
                        <td className="px-3 py-3">
                          <StatusBadge status={business.status} />
                        </td>
                        <td className="px-3 py-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => selectBusiness(business)}
                          >
                            View
                          </Button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="px-3 py-8 text-center text-muted-foreground">
                        No leads found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>
                Page {page} of {pages || 1}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => void loadBusinesses(page - 1)}
                  disabled={page <= 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => void loadBusinesses(page + 1)}
                  disabled={page >= pages}
                >
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {selectedBusiness ? (
        <BusinessDetailPanel
          business={selectedBusiness}
          notesDraft={notesDraft}
          followUpDraft={followUpDraft}
          messageDraft={messageDraft}
          demoDraft={demoDraft}
          onNotesChange={setNotesDraft}
          onFollowUpChange={setFollowUpDraft}
          onMessageChange={setMessageDraft}
          onDemoChange={setDemoDraft}
          onSaveNotes={() => void handleNotesSave()}
          onAddFollowUp={() => void handleAddFollowUp()}
          onAddMessage={() => void handleAddMessage()}
          onAddDemo={() => void handleAddDemo()}
          onDelete={() => void handleDeleteBusiness(selectedBusiness.id)}
        />
      ) : null}
    </section>
  );
}

function BusinessDetailPanel({
  business,
  notesDraft,
  followUpDraft,
  messageDraft,
  demoDraft,
  onNotesChange,
  onFollowUpChange,
  onMessageChange,
  onDemoChange,
  onSaveNotes,
  onAddFollowUp,
  onAddMessage,
  onAddDemo,
  onDelete,
}: {
  business: BusinessDetail;
  notesDraft: string;
  followUpDraft: string;
  messageDraft: string;
  demoDraft: string;
  onNotesChange: (value: string) => void;
  onFollowUpChange: (value: string) => void;
  onMessageChange: (value: string) => void;
  onDemoChange: (value: string) => void;
  onSaveNotes: () => void;
  onAddFollowUp: () => void;
  onAddMessage: () => void;
  onAddDemo: () => void;
  onDelete: () => void;
}) {
  return (
    <Card className="mt-4">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>{business.business_name}</CardTitle>
          <CardDescription>
            {[business.category, business.city, business.state].filter(Boolean).join(" · ")}
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <StatusBadge status={business.status} />
          <Button variant="outline" size="sm" onClick={onDelete}>
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Delete
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-4">
          <InfoGrid business={business} />
          <div>
            <label className="text-sm font-medium">Notes</label>
            <textarea
              className="mt-2 min-h-28 w-full rounded-md border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
              value={notesDraft}
              onChange={(event) => onNotesChange(event.target.value)}
            />
            <Button className="mt-2" size="sm" onClick={onSaveNotes}>
              Save Notes
            </Button>
          </div>
        </div>
        <div className="grid gap-4">
          <HistorySection
            title="Demo history"
            items={business.demos.map((demo) => demo.demo_url ?? demo.notes ?? "Demo")}
          />
          <div className="flex gap-2">
            <input
              className="h-9 flex-1 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="https://demo.example"
              value={demoDraft}
              onChange={(event) => onDemoChange(event.target.value)}
            />
            <Button size="sm" onClick={onAddDemo}>
              Add Demo
            </Button>
          </div>
          <HistorySection
            title="Messages"
            items={business.messages.map((message) => message.message)}
          />
          <div className="flex gap-2">
            <input
              className="h-9 flex-1 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="Message sent to lead"
              value={messageDraft}
              onChange={(event) => onMessageChange(event.target.value)}
            />
            <Button size="sm" onClick={onAddMessage}>
              Add Message
            </Button>
          </div>
          <HistorySection
            title="Follow-ups"
            items={business.follow_ups.map(
              (followUp) => `${new Date(followUp.date).toLocaleString()} ${followUp.notes ?? ""}`,
            )}
          />
          <div className="flex gap-2">
            <input
              className="h-9 flex-1 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
              type="datetime-local"
              value={followUpDraft}
              onChange={(event) => onFollowUpChange(event.target.value)}
            />
            <Button size="sm" onClick={onAddFollowUp}>
              Add Follow-up
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function InfoGrid({ business }: { business: BusinessDetail }) {
  const rows = [
    ["Phone", business.phone_number],
    ["Email", business.email],
    ["Address", business.address],
    ["Website", business.website],
    ["Google Maps", business.google_maps_url],
    ["Justdial", business.justdial_url],
    ["Rating", business.rating ? `${business.rating} (${business.review_count ?? 0})` : null],
  ];

  return (
    <div className="grid gap-2 text-sm">
      {rows.map(([label, value]) => (
        <div
          key={label}
          className="grid grid-cols-[120px_1fr] gap-3 rounded-md border bg-background px-3 py-2"
        >
          <span className="text-muted-foreground">{label}</span>
          <span className="break-words font-medium">{value || "-"}</span>
        </div>
      ))}
    </div>
  );
}

function HistorySection({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border bg-background p-4">
      <p className="font-medium">{title}</p>
      <div className="mt-3 space-y-2 text-sm text-muted-foreground">
        {items.length ? (
          items.map((item, index) => <p key={`${title}-${index}`}>{item}</p>)
        ) : (
          <p>No records yet</p>
        )}
      </div>
    </div>
  );
}

function TextInput({
  label,
  value,
  onChange,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
}) {
  return (
    <label className="grid gap-1 text-sm font-medium">
      {label}
      <input
        className="h-9 rounded-md border bg-background px-3 text-sm font-normal outline-none focus:ring-2 focus:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
      />
    </label>
  );
}

function TextArea({
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
      <textarea
        className="min-h-20 rounded-md border bg-background p-3 text-sm font-normal outline-none focus:ring-2 focus:ring-ring"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function Select({
  value,
  onChange,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}) {
  return (
    <select
      className="h-9 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      {children}
    </select>
  );
}

function StatusBadge({ status }: { status: BusinessStatus }) {
  return <Badge className={cn("border", statusClasses[status])}>{formatStatus(status)}</Badge>;
}

function formatStatus(status: BusinessStatus): string {
  return status
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong";
}
