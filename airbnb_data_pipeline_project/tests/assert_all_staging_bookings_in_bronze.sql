{{ config(severity = 'error') }}

-- Returns any booking_id that exists in Staging but is missing from Bronze
with staging_data as (
    select distinct BOOKING_ID
    from {{ source('staging', 'BOOKINGS') }}
),

bronze_data as (
    select distinct BOOKING_ID
    from {{ ref('bronze_bookings') }}
)

select
    s.BOOKING_ID
from staging_data s
left join bronze_data b
    on s.BOOKING_ID = b.BOOKING_ID
where b.BOOKING_ID is null