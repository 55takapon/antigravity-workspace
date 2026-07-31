-- 体重記録テーブル
-- Supabase ダッシュボードの SQL Editor にそのまま貼り付けて実行する

create table if not exists public.weights (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid()
    references auth.users (id) on delete cascade,
  recorded_at timestamptz not null default now(),
  weight_kg numeric(5, 2) not null check (weight_kg > 0 and weight_kg < 500),
  note text,
  created_at timestamptz not null default now()
);

-- 一覧・グラフはユーザーごとの新しい順で引くため、その並びに合わせる
create index if not exists weights_user_recorded_idx
  on public.weights (user_id, recorded_at desc);

-- 1日に複数回測る想定のため、日付のユニーク制約は付けない
