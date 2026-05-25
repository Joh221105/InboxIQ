# InboxIQ Security Review

Date: 2026-05-25

## Checks Run

- Secret scan with `rg` for common API key names and key-like values.
- Verified committed env templates exist at `backend/.env.example` and `frontend/.env.example`.
- Verified `.gitignore` excludes `.env` and `.env.local` while allowing `.env.example`.
- Reviewed backend router access patterns for raw SQL and authenticated dependencies.
- Reviewed Supabase RLS migrations and adversarial RLS test script.
- Ran `npm audit --omit=dev` and `npm audit fix` for non-breaking frontend dependency fixes.

## Findings

- No real leaked API keys were found in committed files.
- Service role key use remains centralized in `backend/app/db/supabase.py`.
- `backend/.env.example` now uses placeholder values that do not resemble real keys.
- `backend/supabase/tests/test_rls.sql` is aligned with the current `contact_tags` schema.
- `backend/supabase/migrations/016_security_hardening.sql` restricts public execution of SECURITY DEFINER helper functions and adds an `emails.ai_category` check constraint.

## Remaining Risk

- `npm audit --omit=dev` still reports 2 production advisories: Next.js and its bundled PostCSS. The automated fix requires `npm audit fix --force`, which would upgrade Next.js to 16.x. The project is locked to Next.js 14, so this needs an explicit dependency-upgrade decision rather than an automatic breaking upgrade.
- OAuth tokens are stored server-side in Supabase JSONB as designed, but application-level encryption is not implemented yet despite the optional `TOKEN_ENCRYPTION_KEY` setting.
