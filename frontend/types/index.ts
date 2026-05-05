export type User = {
  id: string;
  email: string;
  default_context: "Job Hunting" | "Shopping" | "School Application" | "Daily";
  created_at: string;
};

export type ConnectedAccount = {
  id: string;
  user_id: string;
  provider: string;
  email: string;
  color: string | null;
  token_expiry: string | null;
  created_at: string;
};

export type Email = {
  id: string;
  user_id: string;
  account_id: string;
  gmail_id: string;
  thread_id: string | null;
  subject: string | null;
  sender: string | null;
  snippet: string | null;
  received_at: string | null;
  is_read: boolean;
  labels: string[];
  ai_summary: string | null;
  ai_category: string | null;
};

export type ContactTag = {
  id: string;
  user_id: string;
  email: string;
  tag: string;
  created_at: string;
};
