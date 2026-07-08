drop policy if exists book_comments_public_insert_pending on public.book_comments;
drop policy if exists book_comments_anon_insert_pending on public.book_comments;
drop policy if exists book_comments_authenticated_insert_pending on public.book_comments;

create policy book_comments_anon_insert_pending
  on public.book_comments
  for insert
  to anon
  with check (
    status = 'pending'
    and user_id is null
    and char_length(body) between 2 and 2000
    and char_length(visitor_name) between 1 and 80
  );

create policy book_comments_authenticated_insert_pending
  on public.book_comments
  for insert
  to authenticated
  with check (
    status = 'pending'
    and char_length(body) between 2 and 2000
    and char_length(visitor_name) between 1 and 80
    and (user_id is null or user_id = (select auth.uid()))
  );
