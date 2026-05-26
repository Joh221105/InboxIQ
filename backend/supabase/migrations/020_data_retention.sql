-- 020_data_retention.sql
-- Delete emails older than each user's configured data retention window.

CREATE OR REPLACE FUNCTION public.apply_data_retention()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    deleted_count INTEGER := 0;
    _count INTEGER;
BEGIN
    WITH to_delete AS (
        SELECT e.id
        FROM public.emails e
        JOIN public.users u ON u.id = e.user_id
        WHERE u.data_retention_days IS NOT NULL
          AND e.received_at < now() - (u.data_retention_days * INTERVAL '1 day')
    )
    DELETE FROM public.emails
    WHERE id IN (SELECT id FROM to_delete);

    GET DIAGNOSTICS _count = ROW_COUNT;
    deleted_count := _count;
    RETURN deleted_count;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.apply_data_retention() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.apply_data_retention() TO service_role;
