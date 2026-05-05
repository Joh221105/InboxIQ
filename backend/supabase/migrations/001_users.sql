-- Users profile table (mirrors auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL UNIQUE,
    default_context TEXT NOT NULL DEFAULT 'Daily'
        CHECK (default_context IN ('Job Hunting', 'Shopping', 'School Application', 'Daily')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'users_select_own'
    ) THEN
        CREATE POLICY users_select_own ON public.users
            FOR SELECT USING (auth.uid() = id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'users_update_own'
    ) THEN
        CREATE POLICY users_update_own ON public.users
            FOR UPDATE USING (auth.uid() = id);
    END IF;
END $$;
