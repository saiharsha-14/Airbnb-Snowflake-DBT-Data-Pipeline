{{ config(severity = 'error') }}

-- Identifies negative financial values ingested into bronze_bookings
select
    BOOKING_ID,
    BOOKING_AMOUNT,
    CLEANING_FEE,
    SERVICE_FEE
from {{ ref('bronze_bookings') }}
where BOOKING_AMOUNT < 0
   or CLEANING_FEE < 0
   or SERVICE_FEE < 0