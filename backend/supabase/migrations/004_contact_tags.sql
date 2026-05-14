-- Tags associated with sender email addresses or domains
CREATE TABLE IF NOT EXISTS public.contact_tags (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  identifier  TEXT NOT NULL,          -- email address or @domain.com
  tag         TEXT NOT NULL CHECK (tag IN ('professor', 'friend', 'recruiter', 'custom')),
  custom_label TEXT,                  -- only set when tag = 'custom'
  color       TEXT NOT NULL DEFAULT '#6b7280',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, identifier),
  CHECK (tag = 'custom' OR custom_label IS NULL)
);

CREATE INDEX IF NOT EXISTS contact_tags_user_id_idx ON public.contact_tags(user_id);

ALTER TABLE public.contact_tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own tags" ON public.contact_tags
  FOR ALL USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
