-- Include contact tag assignment in the atomic email upsert used by Gmail sync.

CREATE OR REPLACE FUNCTION public.upsert_email_record(
    p_account_id     UUID,
    p_user_id        UUID,
    p_gmail_id       TEXT,
    p_subject        TEXT,
    p_sender         TEXT,
    p_sender_name    TEXT,
    p_body_text      TEXT,
    p_contact_tag_id UUID,
    p_received_at    TIMESTAMPTZ
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
        (
            account_id,
            user_id,
            gmail_id,
            subject,
            sender,
            sender_name,
            body_text,
            contact_tag_id,
            received_at
        )
    VALUES
        (
            p_account_id,
            p_user_id,
            p_gmail_id,
            p_subject,
            p_sender,
            p_sender_name,
            p_body_text,
            p_contact_tag_id,
            p_received_at
        )
    ON CONFLICT (account_id, gmail_id) DO UPDATE SET
        subject        = EXCLUDED.subject,
        body_text      = EXCLUDED.body_text,
        sender         = EXCLUDED.sender,
        sender_name    = EXCLUDED.sender_name,
        contact_tag_id = EXCLUDED.contact_tag_id
    RETURNING (xmax = 0) INTO _is_insert;

    RETURN CASE WHEN _is_insert THEN 'inserted' ELSE 'updated' END;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.upsert_email_record(
    UUID, UUID, TEXT, TEXT, TEXT, TEXT, TEXT, UUID, TIMESTAMPTZ
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_email_record(
    UUID, UUID, TEXT, TEXT, TEXT, TEXT, TEXT, UUID, TIMESTAMPTZ
) TO service_role;
