export type User = {
  id: string;
  email: string;
  default_context: "Job Hunting" | "Shopping" | "School Application" | "Daily";
  created_at: string;
};

export type ConnectedAccount = {
  id: string;
  email_address: string;
  provider: string;
  color: string | null;
  last_synced: string | null;
  disconnected_at: string | null;
};

export type Email = {
  id: string;
  user_id: string;
  account_id: string;
  gmail_id: string;
  thread_id: string | null;
  subject: string | null;
  sender: string | null;
  received_at: string | null;
  is_read: boolean;
  labels: string[];
  ai_summary: string | null;
  ai_category: string | null;
  triage_category?: TriageCategory | null;
  deadline_extracted?: string | null;
  action_items?: string[];
  ai_processed?: boolean;
  pickup_used?: boolean;
  is_archived: boolean;
  account_color: string | null;
  account_email?: string | null;
  created_at: string;
  contact_tag?: { label: string; color: string } | null;
};

export type EmailListPage = {
  items: Email[];
  next_cursor: string | null;
};

export type TriageCategory = "action_required" | "worth_reading" | "auto_archive";

export type EmailCounts = {
  all: number;
  action_required: number;
  worth_reading: number;
  auto_archive: number;
};

export type EmailBody = {
  body_html: string;
};

export type PickupCode = {
  email_id: string;
  pickup_code: string;
  pickup_expiry: string | null;
  pickup_used_at: string | null;
  retailer: string | null;
  locker_location: string | null;
  sender_email: string | null;
  subject: string | null;
  received_at: string | null;
};

export type PickupCodeList = {
  items: PickupCode[];
};

export type ContactTag = {
  id: string;
  user_id: string;
  email: string;
  tag: string;
  created_at: string;
};
