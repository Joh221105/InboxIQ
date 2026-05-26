ALTER TABLE public.emails
    ADD COLUMN IF NOT EXISTS pickup_used_at TIMESTAMPTZ;
