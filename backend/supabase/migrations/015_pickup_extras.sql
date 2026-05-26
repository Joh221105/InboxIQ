ALTER TABLE public.emails
    ADD COLUMN IF NOT EXISTS retailer TEXT,
    ADD COLUMN IF NOT EXISTS locker_location TEXT;
