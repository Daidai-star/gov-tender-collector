export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface TaskStats {
  last_24h_total_jobs: number;
  last_24h_success_jobs: number;
  last_24h_failed_jobs: number;
  notices_total: number;
}

export interface NoticeListItem {
  id: number;
  title: string;
  tender_type: string;
  region_province: string;
  region_city: string;
  publish_time: string | null;
  has_attachments: boolean;
  attachment_names: string[];
  is_favorited: boolean;
  has_ai_analysis: boolean;
}

export interface NoticeListResponse {
  total: number;
  items: NoticeListItem[];
}

export interface Attachment {
  id: number;
  file_name: string;
  file_type: string;
  file_size: number;
  storage_path: string;
}

export interface AIAnalysis {
  id: number;
  model: string;
  status: string;
  summary: string | null;
  key_requirements: unknown[];
  risk_points: unknown[];
  deadline_items: unknown[];
  raw_json: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
}

export interface NoticeDetail {
  id: number;
  title: string;
  source_url: string;
  tender_type: string;
  region_province: string;
  region_city: string;
  publish_time: string | null;
  content_text: string;
  attachments: Attachment[];
  is_favorited: boolean;
  latest_ai_analysis: AIAnalysis | null;
}

export interface Site {
  id: number;
  name: string;
  base_url: string;
  province: string;
  city: string;
  adapter_key: string;
  crawl_enabled: boolean;
  rate_limit: number;
  schedule_group: string;
  parser_rules: Record<string, unknown>;
  created_at: string;
}

export interface UserOut {
  id: number;
  username: string;
  roles: string[];
  created_at: string;
}
