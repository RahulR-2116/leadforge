const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type HealthCheck = {
  service: string;
  status: string;
  environment: string;
  database: string;
};

export async function getHealthCheck(): Promise<HealthCheck> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthCheck>;
}

export const BUSINESS_STATUSES = [
  "NEW",
  "CONTACTED",
  "REPLIED",
  "DEMO_REQUESTED",
  "DEMO_SENT",
  "NEGOTIATING",
  "CLIENT",
  "LOST",
] as const;

export type BusinessStatus = (typeof BUSINESS_STATUSES)[number];

export type Business = {
  id: number;
  business_name: string;
  category: string | null;
  phone_number: string | null;
  email: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  website: string | null;
  has_website: boolean;
  google_maps_url: string | null;
  justdial_url: string | null;
  rating: number | null;
  review_count: number | null;
  status: BusinessStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type FollowUp = {
  id: number;
  business_id: number;
  date: string;
  completed: boolean;
  notes: string | null;
};

export type Demo = {
  id: number;
  business_id: number;
  demo_url: string | null;
  video_url: string | null;
  notes: string | null;
  created_at: string;
};

export type Message = {
  id: number;
  business_id: number;
  message: string;
  sent: boolean;
  sent_at: string | null;
};

export type BusinessDetail = Business & {
  follow_ups: FollowUp[];
  demos: Demo[];
  messages: Message[];
};

export type BusinessList = {
  items: Business[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type BusinessStats = {
  total_businesses: number;
  contacted: number;
  replies: number;
  demos_sent: number;
  clients_won: number;
  lost: number;
  businesses_with_websites: number;
  businesses_without_websites: number;
};

export type ScrapeJobStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";

export type ScrapeJob = {
  job_id: string;
  source: string;
  status: ScrapeJobStatus;
  category: string;
  city: string;
  maximum_results: number;
  current_task: string;
  current_business: string | null;
  progress: number;
  businesses_found: number;
  businesses_processed: number;
  businesses_imported: number;
  duplicates_skipped: number;
  errors: string[];
  eta_seconds: number | null;
  log_file: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type GoogleMapsScrapePayload = {
  category: string;
  city: string;
  maximum_results: number;
};

export type BusinessPayload = {
  business_name: string;
  category?: string | null;
  phone_number?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  website?: string | null;
  has_website?: boolean;
  google_maps_url?: string | null;
  justdial_url?: string | null;
  rating?: number | null;
  review_count?: number | null;
  status?: BusinessStatus;
  notes?: string | null;
};

export type BusinessQuery = {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  city?: string;
  state?: string;
  has_website?: string;
  status?: BusinessStatus | "";
  sort_by?: string;
  sort_direction?: "asc" | "desc";
};

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string | { msg?: string }[] };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (Array.isArray(payload.detail) && payload.detail[0]?.msg) {
        message = payload.detail[0].msg;
      }
    } catch {
      // Keep the generic HTTP error when the response is not JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function buildQuery(params: BusinessQuery): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function getBusinessStats(): Promise<BusinessStats> {
  return apiRequest<BusinessStats>("/api/v1/businesses/stats");
}

export function listBusinesses(params: BusinessQuery): Promise<BusinessList> {
  return apiRequest<BusinessList>(`/api/v1/businesses${buildQuery(params)}`);
}

export function getBusiness(id: number): Promise<BusinessDetail> {
  return apiRequest<BusinessDetail>(`/api/v1/businesses/${id}`);
}

export function createBusiness(payload: BusinessPayload): Promise<BusinessDetail> {
  return apiRequest<BusinessDetail>("/api/v1/businesses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateBusiness(
  id: number,
  payload: Partial<BusinessPayload>,
): Promise<BusinessDetail> {
  return apiRequest<BusinessDetail>(`/api/v1/businesses/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteBusiness(id: number): Promise<void> {
  return apiRequest<void>(`/api/v1/businesses/${id}`, { method: "DELETE" });
}

export function bulkDeleteBusinesses(ids: number[]): Promise<void> {
  const query = ids.map((id) => `ids=${id}`).join("&");
  return apiRequest<void>(`/api/v1/businesses/bulk?${query}`, { method: "DELETE" });
}

export function bulkUpdateBusinessStatus(
  ids: number[],
  status: BusinessStatus,
): Promise<Business[]> {
  const query = ids.map((id) => `ids=${id}`).join("&");
  return apiRequest<Business[]>(`/api/v1/businesses/bulk/status?${query}`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
}

export function addFollowUp(
  businessId: number,
  payload: { date: string; completed: boolean; notes?: string | null },
): Promise<FollowUp> {
  return apiRequest<FollowUp>(`/api/v1/businesses/${businessId}/follow-ups`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addDemo(
  businessId: number,
  payload: { demo_url?: string | null; video_url?: string | null; notes?: string | null },
): Promise<Demo> {
  return apiRequest<Demo>(`/api/v1/businesses/${businessId}/demos`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addMessage(
  businessId: number,
  payload: { message: string; sent: boolean; sent_at?: string | null },
): Promise<Message> {
  return apiRequest<Message>(`/api/v1/businesses/${businessId}/messages`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function exportUrl(format: "csv" | "xlsx"): string {
  return `${API_BASE_URL}/api/v1/businesses/export?format=${format}`;
}

export function startGoogleMapsScrape(payload: GoogleMapsScrapePayload): Promise<ScrapeJob> {
  return apiRequest<ScrapeJob>("/api/v1/scraper/google-maps/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getScrapeJob(jobId: string): Promise<ScrapeJob> {
  return apiRequest<ScrapeJob>(`/api/v1/scraper/jobs/${jobId}`);
}

export function getLatestScrapeJob(): Promise<ScrapeJob | null> {
  return apiRequest<ScrapeJob | null>("/api/v1/scraper/jobs/latest");
}
