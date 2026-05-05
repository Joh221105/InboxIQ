-- Tags associated with sender email addresses
CREATE TABLE IF NOT EXISTS public.contact_tags (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL,
    tag         TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, email, tag)
);

CREATE INDEX IF NOT EXISTS contact_tags_user_id_idx ON public.contact_tags(user_id);

ALTER TABLE public.contact_tags ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'contact_tags' AND policyname = 'contact_tags_select_own'
    ) THEN
        CREATE POLICY contact_tags_select_own ON public.contact_tags
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'contact_tags' AND policyname = 'contact_tags_insert_own'
    ) THEN
        CREATE POLICY contact_tags_insert_own ON public.contact_tags
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'contact_tags' AND policyname = 'contact_tags_delete_own'
    ) THEN
        CREATE POLICY contact_tags_delete_own ON public.contact_tags
            FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;
