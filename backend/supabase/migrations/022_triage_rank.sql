-- Rank emails by triage priority so the inbox can be keyset-paginated with a
-- single ORDER BY (priority, recency) in the database instead of re-sorting
-- each page in the API.
--
-- Emails without a category (still being analyzed, or AI unavailable) rank
-- with worth_reading so they are never buried below auto-archived mail.
ALTER TABLE public.emails
    ADD COLUMN IF NOT EXISTS triage_rank smallint
    GENERATED ALWAYS AS (
        CASE ai_category
            WHEN 'action_required' THEN 1
            WHEN 'auto_archive' THEN 3
            ELSE 2
        END
    ) STORED;

CREATE INDEX IF NOT EXISTS emails_inbox_order_idx
    ON public.emails (user_id, is_archived, triage_rank, received_at DESC, id DESC);
