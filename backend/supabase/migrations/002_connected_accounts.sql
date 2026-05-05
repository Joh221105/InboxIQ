-- Gmail / OAuth connected accounts
CREATE TABLE IF NOT EXISTS public.connected_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL DEFAULT 'gmail',
    email           TEXT NOT NULL,
    oauth_token     TEXT,         -- encrypted at app layer
    refresh_token   TEXT,         -- encrypted at app layer
    token_expiry    TIMESTAMPTZ,
    color           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, email)
);

CREATE INDEX IF NOT EXISTS connected_accounts_user_id_idx ON public.connected_accounts(user_id);

ALTER TABLE public.connected_accounts ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'connected_accounts' AND policyname = 'accounts_select_own'
    ) THEN
        CREATE POLICY accounts_select_own ON public.connected_accounts
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'connected_accounts' AND policyname = 'accounts_insert_own'
    ) THEN
        CREATE POLICY accounts_insert_own ON public.connected_accounts
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'connected_accounts' AND policyname = 'accounts_update_own'
    ) THEN
        CREATE POLICY accounts_update_own ON public.connected_accounts
            FOR UPDATE USING (auth.uid() = user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'connected_accounts' AND policyname = 'accounts_delete_own'
    ) THEN
        CREATE POLICY accounts_delete_own ON public.connected_accounts
            FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;
