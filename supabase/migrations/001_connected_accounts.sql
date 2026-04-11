-- Gmail (and future) OAuth tokens — written only by the FastAPI backend using the service role.
-- RLS: no direct anon access; backend bypasses RLS with service_role.

create table if not exists public.connected_accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  email_address text not null,
  provider text not null check (provider in ('gmail', 'outlook')),
  oauth_token jsonb not null,
  color text not null default '#4285F4',
  last_synced timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint connected_accounts_user_email_provider unique (user_id, email_address, provider)
);

create index if not exists connected_accounts_user_id_idx
  on public.connected_accounts (user_id);

alter table public.connected_accounts enable row level security;

drop policy if exists "Users read own connected accounts" on public.connected_accounts;

-- Authenticated users can read their own rows (optional; service role still used for writes).
create policy "Users read own connected accounts"
  on public.connected_accounts
  for select
  to authenticated
  using (auth.uid() = user_id);

-- No insert/update/delete for anon/authenticated clients — only service_role.

create or replace function public.set_connected_accounts_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists connected_accounts_set_updated_at on public.connected_accounts;
create trigger connected_accounts_set_updated_at
  before update on public.connected_accounts
  for each row
  execute function public.set_connected_accounts_updated_at();
