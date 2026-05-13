-- 010_email_search.sql
-- Adds generated full-text search support for the shipped Issue 1C email schema.

ALTER TABLE public.emails
    ADD COLUMN IF NOT EXISTS search_tsv tsvector
    GENERATED ALWAYS AS (
        to_tsvector('english',
            coalesce(subject, '') || ' ' ||
            coalesce(sender, '') || ' ' ||
            coalesce(body_text, '') || ' ' ||
            coalesce(snippet, '')
        )
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_emails_search
    ON public.emails USING GIN (search_tsv);
