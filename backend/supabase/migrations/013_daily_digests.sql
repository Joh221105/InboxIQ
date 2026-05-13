CREATE TABLE IF NOT EXISTS public.daily_digests (
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    digest_date DATE NOT NULL,
    payload JSONB NOT NULL,
    degraded BOOLEAN DEFAULT false,
    generated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, digest_date)
);

ALTER TABLE public.daily_digests ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'daily_digests' AND policyname = 'digest_user_select'
    ) THEN
        CREATE POLICY digest_user_select ON public.daily_digests
            FOR SELECT USING (user_id = auth.uid());
    END IF;
END $$;
