create extension if not exists pgcrypto;

create table if not exists public.books (
  id text primary key,
  title text not null,
  language text not null default 'zh-Hant',
  status text not null default 'published',
  created_at timestamptz not null default now()
);

insert into public.books (id, title, language, status)
values (
  'wuxing-theory-book3',
  '宇宙是光之流體：物性論作為新的科學範式',
  'zh-Hant',
  'published'
)
on conflict (id) do update
set title = excluded.title,
    language = excluded.language,
    status = excluded.status;

create table if not exists public.user_favorites (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  item_id text not null,
  item_type text not null default 'chapter',
  item_title text not null,
  item_url text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_favorites_item_type_check
    check (item_type in ('book', 'chapter', 'resource'))
);

create unique index if not exists user_favorites_user_item_uidx
  on public.user_favorites (user_id, item_id);

create index if not exists user_favorites_user_updated_idx
  on public.user_favorites (user_id, updated_at desc);

create table if not exists public.book_comments (
  id uuid primary key default gen_random_uuid(),
  book_id text not null references public.books(id) on delete cascade,
  chapter_path text not null,
  chapter_title text not null default '',
  user_id uuid references auth.users(id) on delete set null,
  visitor_name text not null default '匿名讀者',
  body text not null,
  status text not null default 'pending',
  created_at timestamptz not null default now(),
  approved_at timestamptz,
  constraint book_comments_status_check
    check (status in ('pending', 'approved', 'rejected')),
  constraint book_comments_body_length_check
    check (char_length(body) between 2 and 2000),
  constraint book_comments_visitor_name_length_check
    check (char_length(visitor_name) between 1 and 80)
);

create index if not exists book_comments_public_idx
  on public.book_comments (book_id, chapter_path, status, created_at desc);

create index if not exists book_comments_user_idx
  on public.book_comments (user_id, created_at desc)
  where user_id is not null;

create table if not exists public.download_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  book_id text not null references public.books(id) on delete cascade,
  format text not null,
  created_at timestamptz not null default now(),
  client_info jsonb not null default '{}'::jsonb,
  constraint download_requests_format_check
    check (format in ('docx', 'markdown'))
);

create index if not exists download_requests_user_created_idx
  on public.download_requests (user_id, created_at desc);

create index if not exists download_requests_book_created_idx
  on public.download_requests (book_id, created_at desc);

alter table public.books enable row level security;
alter table public.user_favorites enable row level security;
alter table public.book_comments enable row level security;
alter table public.download_requests enable row level security;

drop policy if exists books_public_select on public.books;
create policy books_public_select
  on public.books
  for select
  to anon, authenticated
  using (status = 'published');

drop policy if exists user_favorites_own_select on public.user_favorites;
create policy user_favorites_own_select
  on public.user_favorites
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists user_favorites_own_insert on public.user_favorites;
create policy user_favorites_own_insert
  on public.user_favorites
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists user_favorites_own_update on public.user_favorites;
create policy user_favorites_own_update
  on public.user_favorites
  for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists user_favorites_own_delete on public.user_favorites;
create policy user_favorites_own_delete
  on public.user_favorites
  for delete
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists book_comments_approved_select on public.book_comments;
create policy book_comments_approved_select
  on public.book_comments
  for select
  to anon, authenticated
  using (status = 'approved');

drop policy if exists book_comments_public_insert_pending on public.book_comments;
create policy book_comments_public_insert_pending
  on public.book_comments
  for insert
  to anon, authenticated
  with check (
    status = 'pending'
    and char_length(body) between 2 and 2000
    and char_length(visitor_name) between 1 and 80
    and (user_id is null or user_id = (select auth.uid()))
  );

drop policy if exists download_requests_own_select on public.download_requests;
create policy download_requests_own_select
  on public.download_requests
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists download_requests_own_insert on public.download_requests;
create policy download_requests_own_insert
  on public.download_requests
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'private-downloads',
  'private-downloads',
  false,
  52428800,
  array[
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/markdown',
    'text/plain',
    'application/octet-stream'
  ]
)
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;
