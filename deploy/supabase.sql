-- Run in the SQL Editor of a dedicated Supabase Free project.
-- Only backend service_role can call these functions. No public table policies.
create table if not exists public.scholarbot_sessions (
    id text primary key,
    payload jsonb not null,
    revision bigint not null default 1,
    expires_at timestamptz not null default now() + interval '24 hours'
);
alter table public.scholarbot_sessions enable row level security;
revoke all on public.scholarbot_sessions from anon, authenticated;

create table if not exists public.scholarbot_quota (
    id integer primary key check (id = 1),
    minute_start timestamptz not null,
    day_start timestamptz not null,
    minute_count integer not null default 0,
    day_count integer not null default 0
);
alter table public.scholarbot_quota enable row level security;
revoke all on public.scholarbot_quota from anon, authenticated;

create or replace function public.scholarbot_load_session(p_id text)
returns jsonb language sql security definer set search_path = public as $$
    select jsonb_build_object('payload', payload, 'revision', revision)
    from scholarbot_sessions where id = p_id and expires_at > now();
$$;

create or replace function public.scholarbot_save_session(p_id text, p_payload jsonb, p_revision bigint)
returns bigint language plpgsql security definer set search_path = public as $$
declare result bigint;
begin
    if length(p_id) > 128 or octet_length(p_payload::text) > 2000000 then
        raise exception 'session exceeds demo limits';
    end if;
    delete from scholarbot_sessions where expires_at <= now();
    if p_revision = 0 then
        insert into scholarbot_sessions(id, payload) values (p_id, p_payload)
        on conflict do nothing returning revision into result;
    else
        update scholarbot_sessions set payload = p_payload, revision = revision + 1,
            expires_at = now() + interval '24 hours'
        where id = p_id and revision = p_revision returning revision into result;
    end if;
    return result;
end;
$$;

-- Atomic fixed windows: calendar minute and UTC day; no per-instance reset.
create or replace function public.scholarbot_take_quota(p_minute_limit integer, p_day_limit integer)
returns integer language plpgsql security definer set search_path = public as $$
declare q scholarbot_quota%rowtype;
    t timestamptz := clock_timestamp();
    m timestamptz := date_trunc('minute', t);
    d timestamptz := date_trunc('day', t at time zone 'UTC') at time zone 'UTC';
    retry integer := 0;
begin
    insert into scholarbot_quota(id, minute_start, day_start) values (1,m,d) on conflict do nothing;
    select * into q from scholarbot_quota where id = 1 for update;
    -- Evaluate windows after acquiring the lock so waiting requests cannot rewind them.
    t := clock_timestamp();
    m := date_trunc('minute', t);
    d := date_trunc('day', t at time zone 'UTC') at time zone 'UTC';
    if q.minute_start <> m then q.minute_count := 0; end if;
    if q.day_start <> d then q.day_count := 0; end if;
    if p_minute_limit > 0 and q.minute_count >= p_minute_limit then
        retry := greatest(1, ceil(extract(epoch from (m + interval '1 minute' - t)))::integer);
    end if;
    if p_day_limit > 0 and q.day_count >= p_day_limit then
        retry := greatest(retry, 1, ceil(extract(epoch from (d + interval '1 day' - t)))::integer);
    end if;
    if retry = 0 then
        update scholarbot_quota set minute_start=m, day_start=d,
            minute_count=q.minute_count+1, day_count=q.day_count+1 where id=1;
    end if;
    return retry;
end;
$$;

revoke execute on function public.scholarbot_load_session(text) from public, anon, authenticated;
revoke execute on function public.scholarbot_save_session(text,jsonb,bigint) from public, anon, authenticated;
revoke execute on function public.scholarbot_take_quota(integer,integer) from public, anon, authenticated;
grant execute on function public.scholarbot_load_session(text) to service_role;
grant execute on function public.scholarbot_save_session(text,jsonb,bigint) to service_role;
grant execute on function public.scholarbot_take_quota(integer,integer) to service_role;
