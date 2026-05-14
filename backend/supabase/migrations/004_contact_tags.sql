-- Tags associated with sender email addresses or domains
CREATE TABLE contact_tags (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  identifier  TEXT NOT NULL,          -- email address or @domain.com
  tag         TEXT NOT NULL,          -- 'professor' | 'friend' | 'recruiter' | 'custom'
  custom_label TEXT,                  -- only set when tag = 'custom'
  color       TEXT NOT NULL DEFAULT '#6b7280',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, identifier)
);

ALTER TABLE contact_tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own tags" ON contact_tags
  FOR ALL USING (auth.uid() = user_id);
