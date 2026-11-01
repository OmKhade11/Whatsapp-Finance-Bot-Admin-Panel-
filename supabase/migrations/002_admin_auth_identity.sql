-- Link Supabase Auth identities to the existing admin role model.
-- This is additive and does not repurpose application users as administrators.

alter table public.admin_users
    alter column user_id drop not null;

alter table public.admin_users
    add column if not exists auth_user_id uuid;

create unique index if not exists admin_users_auth_user_uidx
    on public.admin_users(auth_user_id)
    where auth_user_id is not null;

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from public.admin_users au
        join public.admin_roles ar on ar.role_id = au.admin_role_id
        where au.auth_user_id = auth.uid()
          and upper(coalesce(au.status, '')) = 'ACTIVE'
          and upper(coalesce(ar.status, '')) = 'ACTIVE'
    );
$$;

revoke all on function public.is_admin() from public;
grant execute on function public.is_admin() to authenticated;

drop policy if exists admin_users_self_read on public.admin_users;
create policy admin_users_self_read
on public.admin_users
for select
to authenticated
using (auth_user_id = auth.uid() or public.is_admin());

drop policy if exists admin_roles_admin_read on public.admin_roles;
create policy admin_roles_admin_read
on public.admin_roles
for select
to authenticated
using (public.is_admin());
