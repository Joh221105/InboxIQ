-- Add optional display name that users can set in Settings.
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS display_name TEXT;
