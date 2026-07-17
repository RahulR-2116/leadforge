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
