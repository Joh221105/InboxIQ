ALTER TABLE public.emails
    ADD COLUMN IF NOT EXISTS ai_attempts INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_ai_attempt_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ai_processed BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS triage_context TEXT,
    ADD COLUMN IF NOT EXISTS deadline_extracted DATE,
    ADD COLUMN IF NOT EXISTS action_items TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS is_pickup_code BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS pickup_code TEXT,
    ADD COLUMN IF NOT EXISTS pickup_expiry DATE,
    ADD COLUMN IF NOT EXISTS pickup_used BOOLEAN NOT NULL DEFAULT false;

CREATE OR REPLACE FUNCTION public.increment_ai_attempts(p_email_id UUID)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    UPDATE public.emails
    SET ai_attempts = COALESCE(ai_attempts, 0) + 1,
        last_ai_attempt_at = now()
    WHERE id = p_email_id;
$$;
