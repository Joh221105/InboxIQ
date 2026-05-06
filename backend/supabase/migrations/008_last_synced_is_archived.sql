-- 008_last_synced_is_archived.sql
-- Adds last_synced to connected_accounts and is_archived to emails

ALTER TABLE public.connected_accounts
    ADD COLUMN IF NOT EXISTS last_synced TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS connected_accounts_last_synced_idx
    ON public.connected_accounts(last_synced);

ALTER TABLE public.emails
    ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT false;
