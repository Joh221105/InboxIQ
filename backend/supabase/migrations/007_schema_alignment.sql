-- 007_schema_alignment.sql
-- Aligns connected_accounts with intended schema:
--   email → email_address, separate token cols → oauth_token JSONB,
--   adds disconnected_at / disconnected_reason

-- 1. Rename email → email_address
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'connected_accounts' AND column_name = 'email'
    ) THEN
        ALTER TABLE public.connected_accounts RENAME COLUMN email TO email_address;
    END IF;
END $$;

-- 2. Fix unique constraint
ALTER TABLE public.connected_accounts
    DROP CONSTRAINT IF EXISTS connected_accounts_user_id_email_key;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'connected_accounts_user_id_email_address_key'
    ) THEN
        ALTER TABLE public.connected_accounts
            ADD CONSTRAINT connected_accounts_user_id_email_address_key
            UNIQUE (user_id, email_address);
    END IF;
END $$;

-- 3. Add temp JSONB column
ALTER TABLE public.connected_accounts
    ADD COLUMN IF NOT EXISTS oauth_token_jsonb JSONB;

-- 4. Backfill from old columns (only while they still exist)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'connected_accounts' AND column_name = 'refresh_token'
    ) THEN
        UPDATE public.connected_accounts
        SET oauth_token_jsonb = json_build_object(
            'access_token',  COALESCE(oauth_token, ''),
            'refresh_token', COALESCE(refresh_token, ''),
            'expires_at',    COALESCE(token_expiry::text, now()::text),
            'scope',         'https://www.googleapis.com/auth/gmail.readonly'
        );
    END IF;
END $$;

-- 5. Drop the three old token columns
ALTER TABLE public.connected_accounts
    DROP COLUMN IF EXISTS refresh_token,
    DROP COLUMN IF EXISTS token_expiry;

-- Drop old TEXT oauth_token (before renaming the JSONB one)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'connected_accounts'
          AND column_name = 'oauth_token'
          AND data_type = 'text'
    ) THEN
        ALTER TABLE public.connected_accounts DROP COLUMN oauth_token;
    END IF;
END $$;

-- 6. Rename temp column to oauth_token
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'connected_accounts' AND column_name = 'oauth_token_jsonb'
    ) THEN
        ALTER TABLE public.connected_accounts
            RENAME COLUMN oauth_token_jsonb TO oauth_token;
    END IF;
END $$;

-- 7. Add disconnect tracking columns
ALTER TABLE public.connected_accounts
    ADD COLUMN IF NOT EXISTS disconnected_at     TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS disconnected_reason TEXT;
