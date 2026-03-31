// ── Enums / union types ──────────────────────────────────────────────────────

export type ClientStatus =
  | "DRAFT"
  | "KYC_PENDING"
  | "AGREEMENT_SENT"
  | "SIGNED"
  | "ACTIVE";

export type ClientTier = "ESSENTIAL" | "GROWTH" | "PREMIUM" | "ELITE";

export type RiskBand = "LOW" | "MODERATE" | "AGGRESSIVE";

export type UserRole =
  | "advisor"
  | "admin"
  | "compliance_officer"
  | "associate";

// ── Domain models ────────────────────────────────────────────────────────────

export interface Client {
  id: string;
  firm_id: string;
  advisor_id: string;
  status: ClientStatus;
  tier: ClientTier;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string | null;
  date_of_birth: string | null;
  address_street: string | null;
  address_city: string | null;
  address_state: string | null;
  address_zip: string | null;
  employment_status: string | null;
  annual_income: number | null;
  tax_filing_status: string | null;
  ai_consent: boolean;
  tier_assigned_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RiskProfile {
  id: string;
  client_id: string;
  score: number;
  band: RiskBand;
  answers: Record<string, unknown>;
  scored_at: string;
  created_at: string;
}

// ── Request payloads ─────────────────────────────────────────────────────────

export interface ClientCreatePayload {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  date_of_birth?: string;
  ssn?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  employment_status?: string;
  annual_income?: number;
  tax_filing_status?: string;
  ai_consent: boolean;
}

export interface RiskProfileCreatePayload {
  answers: number[];
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface CurrentUser {
  sub: string;
  email: string;
  name: string;
  role: UserRole;
  advisor_id: string;
  firm_id: string;
}
