-- RLS adversarial tests
-- Run in Supabase SQL editor authenticated as user_a (replace UUIDs with real test user IDs)
-- All queries must return 0 rows

-- Setup: replace these with actual test user UUIDs
-- user_a_id = the authenticated user running these queries
-- user_b_id = a different user whose data should be inaccessible

-- 1. Cannot read another user's profile row
SELECT * FROM public.users
WHERE id = '<user_b_id>';

-- 2. Cannot read another user's connected accounts
SELECT * FROM public.connected_accounts
WHERE user_id = '<user_b_id>';

-- 3. Cannot read another user's emails
SELECT * FROM public.emails
WHERE user_id = '<user_b_id>';

-- 4. Cannot read another user's contact tags
SELECT * FROM public.contact_tags
WHERE user_id = '<user_b_id>';

-- 5. Cannot read another user's oauth token (via connected_accounts)
SELECT oauth_token FROM public.connected_accounts
WHERE user_id = '<user_b_id>';

-- 6. Cannot update another user's profile
UPDATE public.users
SET default_context = 'Shopping'
WHERE id = '<user_b_id>'
RETURNING id;

-- 7. Cannot insert email on behalf of another user
INSERT INTO public.emails (user_id, account_id, gmail_id, subject)
VALUES ('<user_b_id>', gen_random_uuid(), 'fake-gmail-id', 'injected subject')
RETURNING id;

-- 8. Cannot delete another user's contact tag
DELETE FROM public.contact_tags
WHERE user_id = '<user_b_id>'
RETURNING id;
