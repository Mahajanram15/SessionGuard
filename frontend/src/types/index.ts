export type SecurityDecision = 'ALLOW' | 'CHALLENGE' | 'RATE_LIMIT' | 'BLOCK';

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  components: Record<string, string>;
}

export interface RiskSignals {
  browser_score: number;
  api_anomaly_score: number;
  api_structure_score: number;
  sequence_score: number;
  frequency_score: number;
  cross_layer_discordance: number;
}

export interface RiskResponse {
  session_id: string;
  behavioral_integrity_score: number;
  signals: RiskSignals;
  decision: {
    action: SecurityDecision;
    reason: string;
    enacted_at: string;
  };
  last_evaluated_at: string;
}

export interface DashboardStats {
  total_sessions: number;
  active_sessions: number;
  average_risk_score: number;
  decision_distribution: Record<SecurityDecision, number>;
  recent_flagged_sessions: Array<{
    session_id: string;
    risk_score: number;
    decision: string;
    primary_reason: string;
    timestamp: string;
  }>;
}

// ------------------------------------------------------------------------------
// Mock Domain & API Telemetry Types (Experiment B)
// ------------------------------------------------------------------------------

export interface ProductItem {
  id: string;
  name: string;
  category: string;
  price: number;
  rating: number;
  description: string;
  in_stock: boolean;
}

export interface ProductListResponse {
  products: ProductItem[];
  total: number;
  page: number;
  page_size: number;
  category?: string | null;
}

export interface ProductDetailResponse {
  id: string;
  name: string;
  category: string;
  price: number;
  rating: number;
  description: string;
  specifications: Record<string, any>;
  in_stock: boolean;
}

export interface SearchResponse {
  query: string;
  results: ProductItem[];
  total_results: number;
  limit: number;
}

export interface SearchFilterResponse {
  filter: string;
  sort: string;
  results: ProductItem[];
  total_results: number;
}

export interface CatalogResponse {
  category?: string | null;
  categories: string[];
  featured_products: ProductItem[];
  total_catalog_items: number;
}

export interface CartItemResponse {
  status: string;
  item_id: string;
  quantity: number;
  message: string;
}

export interface CheckoutVerifyResponse {
  status: string;
  shipping_method: string;
  currency: string;
  is_valid: boolean;
  message: string;
}

export interface ApiTelemetryRecord {
  session_id: string;
  endpoint: string;
  http_method: string;
  status_code: number;
  response_time_ms: number;
  request_size_bytes?: number;
  response_size_bytes?: number;
  headers_fingerprint?: string;
  client_timestamp?: number;
  param_keys?: string[];
  payload_keys?: string[];
}

export interface DomainApiResult<T> {
  data: T | null;
  error: Error | null;
  status: number;
  responseTimeMs: number;
}

// ------------------------------------------------------------------------------
// LearnSphere E-Learning Domain Types
// ------------------------------------------------------------------------------

export interface QuizOption {
  id: string;
  text: string;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: QuizOption[];
  correct_option_id: string;
  explanation: string;
}

export interface LessonItem {
  id: string;
  title: string;
  duration_minutes: number;
  order: number;
  video_url: string;
  description: string;
  quiz?: QuizQuestion[] | null;
}

export interface CourseItem {
  id: string;
  title: string;
  category: string;
  difficulty: string;
  duration_hours: number;
  instructor: string;
  rating: number;
  review_count: number;
  price: number;
  is_free: boolean;
  description: string;
  thumbnail_url: string;
  lesson_count: number;
}

export interface CourseDetailResponse extends CourseItem {
  learning_objectives: string[];
  prerequisites: string[];
  lessons: LessonItem[];
  enrollment_count: number;
}

export interface CourseListResponse {
  courses: CourseItem[];
  total: number;
  page: number;
  page_size: number;
  category?: string | null;
  difficulty?: string | null;
}

export interface CourseSearchResponse {
  query: string;
  results: CourseItem[];
  total_results: number;
  limit: number;
}

export interface EnrollmentResponse {
  status: string;
  enrollment_id: string;
  course_id: string;
  course_title: string;
  plan_type: string;
  is_demo: boolean;
  enrolled_at: string;
  message: string;
}


