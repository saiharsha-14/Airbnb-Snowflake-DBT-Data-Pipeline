{{ config(severity = 'error') }}

-- Returns an alert row if row counts between Staging and Bronze mismatch
with staging_counts as (
    select 
        'bookings' as table_name, count(*) as staging_cnt from {{ source('staging', 'BOOKINGS') }}
    union all
    select 
        'listings' as table_name, count(*) as staging_cnt from {{ source('staging', 'LISTINGS') }}
    union all
    select 
        'hosts' as table_name, count(*) as staging_cnt from {{ source('staging', 'HOSTS') }}
),

bronze_counts as (
    select 
        'bookings' as table_name, count(*) as bronze_cnt from {{ ref('bronze_bookings') }}
    union all
    select 
        'listings' as table_name, count(*) as bronze_cnt from {{ ref('bronze_listings') }}
    union all
    select 
        'hosts' as table_name, count(*) as bronze_cnt from {{ ref('bronze_hosts') }}
)

select
    s.table_name,
    s.staging_cnt,
    b.bronze_cnt,
    abs(s.staging_cnt - b.bronze_cnt) as diff_count
from staging_counts s
join bronze_counts b
    on s.table_name = b.table_name
where s.staging_cnt != b.bronze_cnt