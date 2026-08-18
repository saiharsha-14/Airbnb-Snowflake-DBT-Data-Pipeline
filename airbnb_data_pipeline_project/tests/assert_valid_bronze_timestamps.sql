{{ config(severity = 'warn') }}

-- Flags any bronze records ingested with future timestamps
select
    'bronze_bookings' as entity_name,
    BOOKING_ID as record_id,
    CREATED_AT
from {{ ref('bronze_bookings') }}
where CREATED_AT > current_timestamp()

union all

select
    'bronze_listings' as entity_name,
    LISTING_ID as record_id,
    CREATED_AT
from {{ ref('bronze_listings') }}
where CREATED_AT > current_timestamp()

union all

select
    'bronze_hosts' as entity_name,
    HOST_ID as record_id,
    CREATED_AT
from {{ ref('bronze_hosts') }}
where CREATED_AT > current_timestamp()