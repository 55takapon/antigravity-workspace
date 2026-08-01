-- 1ユーザー1日1件に制限する（同日に複数回記録した場合はアプリ側で upsert して上書きする）
-- 「日」は日本時間（JST, UTC+9固定）の暦日で判定する。
-- Supabase ダッシュボードの SQL Editor にそのまま貼り付けて実行する

-- 1) 既存データに同日複数件があれば、一番新しい記録だけ残して削除する
delete from public.weights w
using (
  select
    id,
    row_number() over (
      partition by user_id, (((recorded_at at time zone 'UTC') + interval '9 hours')::date)
      order by recorded_at desc
    ) as rn
  from public.weights
) dup
where w.id = dup.id and dup.rn > 1;

-- 2) JSTの暦日を保持する生成カラム
--    UTC に固定変換してから +9時間するのは、AT TIME ZONE に固定オフセットの文字列（'UTC'）を
--    使うことで IMMUTABLE な式にするため（生成カラムは IMMUTABLE な式しか使えない）。
alter table public.weights
  add column if not exists local_date date
  generated always as (((recorded_at at time zone 'UTC') + interval '9 hours')::date) stored;

-- 3) 1ユーザー1日1件の一意制約
alter table public.weights
  drop constraint if exists weights_user_local_date_unique;

alter table public.weights
  add constraint weights_user_local_date_unique unique (user_id, local_date);
