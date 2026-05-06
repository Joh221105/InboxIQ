-- 009_upsert_email_fn.sql
-- Atomic email upsert with insert/update detection via xmax trick

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
