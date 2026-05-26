-- 018_user_settings.sql
-- Persist per-user notification and retention preferences.

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS notification_tag_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS data_retention_days INTEGER;

ALTER TABLE public.users
    DROP CONSTRAINT IF EXISTS users_data_retention_days_check;

ALTER TABLE public.users
    ADD CONSTRAINT users_data_retention_days_check
    CHECK (
        data_retention_days IS NULL OR
        data_retention_days BETWEEN 1 AND 3650
    );
