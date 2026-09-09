# Setup

The app runs out of the box with zero setup — it falls back to a local
JSON file for the "products analyzed" counter and the community product
cache. That's fine for testing on your own machine, but **it will not
survive a redeploy on Streamlit Community Cloud**, so the counter would
silently reset and undermine the whole point of showing it. Follow this
once (~10 minutes) to make it permanent.

## 1. Create a free Supabase project

1. Go to https://supabase.com and create a project (free tier).
2. In the project, open the **SQL Editor** and run:

```sql
create table product_cache (
  barcode text primary key,
  data jsonb not null,
  updated_at bigint
);

create table scan_stats (
  id int primary key default 1,
  total bigint not null default 0
);
insert into scan_stats (id, total) values (1, 0);

create or replace function increment_scan_total()
returns bigint
language sql
security definer
as $$
  update scan_stats set total = total + 1 where id = 1
  returning total;
$$;

-- Supabase requires explicit grants for the Data API on new projects.
grant usage on schema public to anon;
grant select, insert, update on public.product_cache to anon;
grant select on public.scan_stats to anon;
grant execute on function increment_scan_total() to anon;

-- Row Level Security: public read/write on the cache (it's not
-- sensitive data — just product info), read-only direct access to
-- scan_stats (writes only happen through the SECURITY DEFINER
-- function above, so nobody can inflate the counter by hand).
alter table product_cache enable row level security;
create policy "public read" on product_cache for select using (true);
create policy "public insert" on product_cache for insert with check (true);
create policy "public update" on product_cache for update using (true);

alter table scan_stats enable row level security;
create policy "public read" on scan_stats for select using (true);
```

3. In **Project Settings -> API**, copy:
   - **Project URL** -> this is `SUPABASE_URL`
   - **anon / public key** -> this is `SUPABASE_KEY` (do **not** use the
     `service_role` key here — this app calls Supabase directly from a
     public Streamlit app, so it should only ever hold the restricted
     `anon` key)

## 2. Add secrets to Streamlit Community Cloud

In your app's dashboard: **Settings -> Secrets**, add:

```toml
SUPABASE_URL = "https://xxxxxxxx.supabase.co"
SUPABASE_KEY = "your-anon-key"
```

Redeploy. The sidebar warning about "local-storage mode" should
disappear once these are picked up.

## 3. (Optional but recommended) Set up the keep-alive Action

This fixes the "waking up takes forever" complaint and keeps the
Supabase free project from pausing after a week of inactivity.

In your GitHub repo: **Settings -> Secrets and variables -> Actions**,
add:

```
STREAMLIT_APP_URL = https://your-app.streamlit.app
SUPABASE_URL      = (same as above)
SUPABASE_KEY      = (same as above)
```

The workflow at `.github/workflows/keepalive.yml` runs every 6 hours
automatically — no further action needed. You can trigger it manually
from the **Actions** tab to test it right away.

## 4. Once you have real usage data, set the accuracy stat

Run `python scripts/evaluate_accuracy.py` after filling in some labeled
samples (see the comments in that file), then paste the result into
`INGREDIENT_RISK_ACCURACY` near the top of `app.py`. Leave it as `None`
until then — the UI shows "coming soon" instead of a placeholder number.
