-- Fetched and processed emails
CREATE TABLE IF NOT EXISTS public.emails (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    account_id      UUID NOT NULL REFERENCES public.connected_accounts(id) ON DELETE CASCADE,
    gmail_id        TEXT NOT NULL,
    thread_id       TEXT,
    subject         TEXT,
    sender          TEXT,
    snippet         TEXT,
    body_text       TEXT,
    received_at     TIMESTAMPTZ,
    is_read         BOOLEAN NOT NULL DEFAULT false,
    labels          TEXT[] NOT NULL DEFAULT '{}',
    ai_summary      TEXT,
    ai_category     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (account_id, gmail_id)
);

CREATE INDEX IF NOT EXISTS emails_user_id_idx ON public.emails(user_id);
CREATE INDEX IF NOT EXISTS emails_account_id_idx ON public.emails(account_id);
CREATE INDEX IF NOT EXISTS emails_received_at_idx ON public.emails(received_at DESC);

ALTER TABLE public.emails ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'emails' AND policyname = 'emails_select_own'
    ) THEN
        CREATE POLICY emails_select_own ON public.emails
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'emails' AND policyname = 'emails_insert_own'
    ) THEN
        CREATE POLICY emails_insert_own ON public.emails
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'emails' AND policyname = 'emails_update_own'
    ) THEN
        CREATE POLICY emails_update_own ON public.emails
            FOR UPDATE USING (auth.uid() = user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'emails' AND policyname = 'emails_delete_own'
    ) THEN
        CREATE POLICY emails_delete_own ON public.emails
            FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;
