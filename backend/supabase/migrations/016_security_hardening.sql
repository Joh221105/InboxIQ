-- 016_security_hardening.sql
-- Tighten SECURITY DEFINER helper access and schema constraints.

CREATE OR REPLACE FUNCTION public.upsert_email_record(
    p_account_id  UUID,
    p_user_id     UUID,
    p_gmail_id    TEXT,
    p_subject     TEXT,
    p_sender      TEXT,
    p_body_text   TEXT,
    p_received_at TIMESTAMPTZ
) RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    _is_insert BOOLEAN;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM public.connected_accounts
        WHERE id = p_account_id
          AND user_id = p_user_id
          AND disconnected_at IS NULL
    ) THEN
        RAISE EXCEPTION 'account does not belong to user'
            USING ERRCODE = '42501';
    END IF;

    INSERT INTO public.emails
        (account_id, user_id, gmail_id, subject, sender, body_text, received_at)
    VALUES
        (p_account_id, p_user_id, p_gmail_id, p_subject, p_sender, p_body_text, p_received_at)
    ON CONFLICT (account_id, gmail_id) DO UPDATE SET
        subject    = EXCLUDED.subject,
        body_text  = EXCLUDED.body_text,
        sender     = EXCLUDED.sender
    RETURNING (xmax = 0) INTO _is_insert;

    RETURN CASE WHEN _is_insert THEN 'inserted' ELSE 'updated' END;
END;
$$;

CREATE OR REPLACE FUNCTION public.increment_ai_attempts(p_email_id UUID)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    UPDATE public.emails
    SET ai_attempts = COALESCE(ai_attempts, 0) + 1,
        last_ai_attempt_at = now()
    WHERE id = p_email_id;
$$;

REVOKE EXECUTE ON FUNCTION public.upsert_email_record(
    UUID, UUID, TEXT, TEXT, TEXT, TEXT, TIMESTAMPTZ
) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.increment_ai_attempts(UUID)
    FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.upsert_email_record(
    UUID, UUID, TEXT, TEXT, TEXT, TEXT, TIMESTAMPTZ
) TO service_role;
GRANT EXECUTE ON FUNCTION public.increment_ai_attempts(UUID)
    TO service_role;

ALTER TABLE public.emails
    DROP CONSTRAINT IF EXISTS emails_ai_category_check;

ALTER TABLE public.emails
    ADD CONSTRAINT emails_ai_category_check
    CHECK (
        ai_category IS NULL OR
        ai_category IN ('action_required', 'worth_reading', 'auto_archive')
    );
