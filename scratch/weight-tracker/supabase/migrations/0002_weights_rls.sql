-- RLS（行レベルセキュリティ）
-- anon key はクライアントに露出する前提のため、安全性はここで担保する。
-- 0001 と続けて必ず実行すること。

alter table public.weights enable row level security;

-- 既存ポリシーがあれば作り直す（再実行可能にするため）
drop policy if exists "weights_select_own" on public.weights;
drop policy if exists "weights_insert_own" on public.weights;
drop policy if exists "weights_update_own" on public.weights;
drop policy if exists "weights_delete_own" on public.weights;

create policy "weights_select_own"
  on public.weights for select
  to authenticated
  using (auth.uid() = user_id);

create policy "weights_insert_own"
  on public.weights for insert
  to authenticated
  with check (auth.uid() = user_id);

create policy "weights_update_own"
  on public.weights for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "weights_delete_own"
  on public.weights for delete
  to authenticated
  using (auth.uid() = user_id);
