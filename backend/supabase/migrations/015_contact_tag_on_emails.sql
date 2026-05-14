-- 015_contact_tag_on_emails.sql
-- Add contact_tag_id FK to emails for Issue 4 (Contact Tagging)

ALTER TABLE public.emails
  ADD COLUMN IF NOT EXISTS contact_tag_id UUID
    REFERENCES public.contact_tags(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_emails_contact_tag
  ON public.emails(contact_tag_id)
  WHERE contact_tag_id IS NOT NULL;
