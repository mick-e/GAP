const API_BASE = '/api/v1';

function getToken(): string | null {
  return localStorage.getItem('token');
}

export function setToken(token: string) {
  localStorage.setItem('token', token);
}

export function clearToken() {
  localStorage.removeItem('token');
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    window.location.href = '/app/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Auth
export const auth = {
  register: (data: { email: string; password: string; name?: string }) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data: { email: string; password: string }) =>
    request<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  me: () => request<{ id: string; email: string; name: string | null; role: string }>('/auth/me'),
  createApiKey: (name: string) =>
    request<{ id: string; name: string; prefix: string; key: string }>('/auth/api-keys', {
      method: 'POST', body: JSON.stringify({ name }),
    }),
  listApiKeys: () => request<Array<{ id: string; name: string; prefix: string }>>('/auth/api-keys'),
  deleteApiKey: (id: string) => request(`/auth/api-keys/${id}`, { method: 'DELETE' }),
  createApiKeyWithRepos: (name: string, repos: string[]) =>
    request<{ id: string; name: string; prefix: string; key: string }>('/auth/api-keys', {
      method: 'POST',
      body: JSON.stringify({ name, repos: repos.length > 0 ? repos : undefined }),
    }),
};

// OAuth
export const oauth = {
  githubAuthorize: () => request<{ url: string }>('/oauth/github/authorize'),
  githubCallback: (code: string) =>
    request<{ access_token: string; user: { email: string; name: string } }>('/oauth/github/callback', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),
  status: () => request<{ github_enabled: boolean }>('/oauth/github/status'),
};

// Org & Repos
export const org = {
  summary: () => request<OrgSummary>('/org'),
  repos: () => request<Repo[]>('/repos'),
};

// Reports
export const reports = {
  activity: (params?: string) => request<ActivityReport>(`/reports/activity${params ? `?${params}` : ''}`),
  quality: (params?: string) => request<QualityReport>(`/reports/quality${params ? `?${params}` : ''}`),
  releases: (params?: string) => request<ReleaseReport>(`/reports/releases${params ? `?${params}` : ''}`),
};

// Repo-specific
export const repo = {
  commits: (name: string, period = 'month') => request(`/repos/${name}/commits?period=${period}`),
  pulls: (name: string, state = 'all') => request(`/repos/${name}/pulls?state=${state}`),
  issues: (name: string, state = 'all') => request(`/repos/${name}/issues?state=${state}`),
  releases: (name: string) => request(`/repos/${name}/releases`),
  security: (name: string) => request(`/repos/${name}/security`),
  workflows: (name: string) => request(`/repos/${name}/workflows`),
};

// Contributors
export const contributors = {
  list: () => request<ContributorProfile[]>('/contributors'),
  get: (username: string) => request<ContributorProfile>(`/contributors/${username}`),
  activity: (username: string, days = 30) => request(`/contributors/${username}/activity?days=${days}`),
  rankings: (metric = 'commits') => request<ContributorRanking[]>(`/contributors/rankings?metric=${metric}`),
};

// Trends
export const trends = {
  overview: (days = 30) => request<TrendOverview>(`/trends/overview?days=${days}`),
  sparklines: (days = 14) => request<Sparkline[]>(`/trends/sparklines?days=${days}`),
  metric: (name: string, days = 30) => request(`/trends/${name}?days=${days}`),
  compare: (metric: string) => request(`/trends/compare?metric=${metric}`),
  predictions: (metric: string, days = 90) =>
    request<TrendPrediction>(`/trends/predictions/${metric}?days=${days}`),
  movingAverage: (metric: string, days = 90, window = 7) =>
    request<MovingAveragePoint[]>(`/trends/moving-average/${metric}?days=${days}&window=${window}`),
};

// Teams
export const teams = {
  metrics: (days = 30) => request<TeamMetrics>(`/teams/metrics?days=${days}`),
  dora: (days = 30) => request<DORAMetrics>(`/teams/dora?days=${days}`),
  compare: (days = 30) => request<TeamComparison[]>(`/teams/compare?days=${days}`),
};

// Custom Metrics
export const customMetrics = {
  list: () => request<CustomMetricResponse[]>('/metrics/custom'),
  get: (id: string) => request<CustomMetricResponse>(`/metrics/custom/${id}`),
  create: (data: CustomMetricCreate) =>
    request<CustomMetricResponse>('/metrics/custom', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<CustomMetricCreate>) =>
    request<CustomMetricResponse>(`/metrics/custom/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => request(`/metrics/custom/${id}`, { method: 'DELETE' }),
  evaluate: (id: string, days = 30) =>
    request<CustomMetricEvaluation>(`/metrics/custom/${id}/evaluate?days=${days}`, { method: 'POST' }),
  variables: () => request<VariableInfo[]>('/metrics/variables'),
};

// Export Schedules
export const exportSchedules = {
  list: () => request<ExportScheduleResponse[]>('/exports/schedules'),
  get: (id: string) => request<ExportScheduleResponse>(`/exports/schedules/${id}`),
  create: (data: ExportScheduleCreate) =>
    request<ExportScheduleResponse>('/exports/schedule', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<ExportScheduleCreate>) =>
    request<ExportScheduleResponse>(`/exports/schedules/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => request(`/exports/schedules/${id}`, { method: 'DELETE' }),
  run: (id: string) => request(`/exports/schedules/${id}/run`, { method: 'POST' }),
};

// Schedules
export const schedules = {
  list: () => request<Schedule[]>('/schedules'),
  get: (id: string) => request<Schedule>(`/schedules/${id}`),
  create: (data: ScheduleCreate) => request<Schedule>('/schedules', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<ScheduleCreate>) =>
    request<Schedule>(`/schedules/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => request(`/schedules/${id}`, { method: 'DELETE' }),
  run: (id: string) => request(`/schedules/${id}/run`, { method: 'POST' }),
  templates: () => request<ScheduleTemplate[]>('/schedules/templates'),
  template: (id: string) => request<ScheduleTemplate>(`/schedules/templates/${id}`),
  createFromTemplate: (data: { template_id: string; recipients: string[]; name?: string }) =>
    request<Schedule>('/schedules/from-template', { method: 'POST', body: JSON.stringify(data) }),
};

// Webhooks
export const webhooks = {
  events: (params?: Record<string, string>) =>
    request<WebhookEvent[]>(`/webhooks/events${params ? `?${new URLSearchParams(params)}` : ''}`),
  event: (id: string) => request<WebhookEventDetail>(`/webhooks/events/${id}`),
  replay: (id: string) => request<WebhookReplayResult>(`/webhooks/events/${id}/replay`, { method: 'POST' }),
  replayBatch: (ids: string[]) =>
    request<WebhookBatchReplayResult>('/webhooks/events/replay-batch', {
      method: 'POST',
      body: JSON.stringify({ event_ids: ids }),
    }),
};

// Audit
export const audit = {
  logs: (params?: Record<string, string>) =>
    request<AuditLogEntry[]>(`/audit/logs${params ? `?${new URLSearchParams(params)}` : ''}`),
  userTrail: (userId: string, limit = 50) =>
    request<AuditLogEntry[]>(`/audit/logs/${userId}?limit=${limit}`),
  stats: () => request<AuditStats>('/audit/stats'),
};

// Notifications
export const notifications = {
  list: (unreadOnly = false, limit = 50) =>
    request<NotificationItem[]>(
      `/notifications?unread_only=${unreadOnly}&limit=${limit}`
    ),
  markRead: (id: string) =>
    request(`/notifications/${id}/read`, { method: 'POST' }),
  markAllRead: () =>
    request('/notifications/read-all', { method: 'POST' }),
  unreadCount: () =>
    request<{ count: number }>('/notifications/unread-count'),
};

export function createNotificationSocket(): WebSocket | null {
  const token = getToken();
  if (!token) return null;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(
    `${proto}//${window.location.host}${API_BASE}/ws/notifications?token=${token}`
  );
  return ws;
}

// Types
export interface NotificationItem {
  id: string;
  type: string;
  title: string;
  message: string;
  data: Record<string, unknown> | null;
  read: boolean;
  created_at: string;
}

export interface OrgSummary {
  org_name: string;
  total_repos: number;
  total_private_repos: number;
  total_public_repos: number;
  total_stars: number;
  total_forks: number;
  total_open_issues: number;
  languages: Record<string, number>;
}

export interface Repo {
  name: string;
  full_name: string;
  description: string | null;
  private: boolean;
  language: string | null;
  stars: number;
  forks: number;
  open_issues: number;
  updated_at: string;
  html_url: string;
}

export interface ActivityReport { org_name: string; period: string; repos: unknown[]; totals: Record<string, number>; }
export interface QualityReport { org_name: string; repos: unknown[]; totals: unknown; }
export interface ReleaseReport { org_name: string; repos: unknown[]; total_releases: number; }

export interface ContributorProfile {
  login: string;
  avatar_url: string | null;
  total_commits: number;
  total_prs: number;
  total_issues: number;
  total_reviews: number;
  repos: string[];
}

export interface ContributorRanking {
  login: string;
  avatar_url: string | null;
  score: number;
  rank: number;
  metric_value: number;
  metric_name: string;
}

export interface TrendComparison {
  metric: string;
  current_value: number;
  previous_value: number;
  change: number;
  change_percent: number;
  direction: string;
}

export interface TrendOverview {
  period: string;
  velocity: TrendComparison;
  quality: TrendComparison;
  engagement: TrendComparison;
}

export interface Sparkline {
  metric: string;
  data: number[];
  labels: string[];
  current: number;
  change_percent: number;
}

export interface TeamMetrics {
  org_name: string;
  total_commits: number;
  total_prs: number;
  total_releases: number;
  contributors_count: number;
  repos_count: number;
  dora: DORAMetrics;
}

export interface DORAMetrics {
  deployment_frequency: number;
  deployment_frequency_unit: string;
  lead_time_hours: number;
  mttr_hours: number;
  change_failure_rate: number;
  rating: string;
}

export interface TeamComparison {
  repo_name: string;
  commits: number;
  prs: number;
  releases: number;
  contributors: number;
  avg_pr_merge_hours: number | null;
  dora: DORAMetrics;
}

export interface Schedule {
  id: string;
  name: string;
  report_type: string;
  schedule: string;
  recipients: string[];
  config: Record<string, unknown>;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
}

export interface ScheduleCreate {
  name: string;
  report_type: string;
  schedule: string;
  recipients: string[];
  config: Record<string, unknown>;
}

export interface ScheduleTemplate {
  id: string;
  name: string;
  description: string;
  report_type: string;
  schedule: string;
  config: Record<string, unknown>;
}

export interface TrendPrediction {
  metric: string;
  trend: string;
  slope: number | null;
  confidence: number | null;
  predictions: Array<{ date: string; value: number; days_ahead: number }>;
  historical: Array<{ date: string; value: number }>;
}

export interface MovingAveragePoint {
  date: string;
  value: number;
  raw_value: number;
}

export interface CustomMetricResponse {
  id: string;
  name: string;
  description: string | null;
  formula: string;
  is_public: boolean;
  created_by: string;
  created_at: string;
}

export interface CustomMetricCreate {
  name: string;
  description?: string;
  formula: string;
  is_public?: boolean;
}

export interface CustomMetricEvaluation {
  metric_id: string;
  metric_name: string;
  formula: string;
  result: number;
  variables: Record<string, number>;
}

export interface VariableInfo {
  name: string;
  description: string;
}

export interface ExportScheduleResponse {
  id: string;
  name: string;
  export_type: string;
  data_source: string;
  schedule: string;
  recipients: string[];
  config: Record<string, unknown> | null;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
}

export interface ExportScheduleCreate {
  name: string;
  export_type: string;
  data_source: string;
  schedule: string;
  recipients: string[];
  config?: Record<string, unknown>;
}

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  status: string;
  created_at: string;
}

export interface AuditStats {
  total: number;
  by_action: Record<string, number>;
  by_day: Record<string, number>;
}

export interface WebhookEvent {
  id: string;
  event_type: string;
  action: string | null;
  repo_name: string | null;
  sender: string | null;
  processed: boolean;
  error: string | null;
  created_at: string;
}

export interface WebhookEventDetail extends WebhookEvent {
  payload: Record<string, unknown>;
}

export interface WebhookReplayResult {
  event_id: string;
  success: boolean;
  error: string | null;
}

export interface WebhookBatchReplayResult {
  total: number;
  successful: number;
  failed: number;
  results: WebhookReplayResult[];
}
