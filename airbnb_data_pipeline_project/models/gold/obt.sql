{{ config(
    materialized = 'table',
    schema = 'gold'
) }}

{% set configs = [
    {
        "table": ref('silver_bookings'),
        "alias": "silver_bookings",
        "columns": "silver_bookings.*"
    },
    {
        "table": ref('silver_listings'),
        "alias": "silver_listings",
        "columns": "silver_listings.property_type, silver_listings.room_type, silver_listings.city, silver_listings.country, silver_listings.accommodates, silver_listings.bedrooms, silver_listings.bathrooms, silver_listings.price_per_night, silver_listings.price_per_night_tag",
        "join_condition": "silver_bookings.listing_id = silver_listings.listing_id"
    },
    {
        "table": ref('silver_hosts'),
        "alias": "silver_hosts",
        "columns": "silver_hosts.host_name, silver_hosts.host_since, silver_hosts.is_superhost, silver_hosts.response_rate_quality",
        "join_condition": "silver_listings.host_id = silver_hosts.host_id"
    }
] %}

SELECT 
    {{ configs[0].columns }},
    {{ configs[1].columns }},
    {{ configs[2].columns }}
FROM
    {% for config in configs %}
        {% if loop.first %}
            {{ config.table }} AS {{ config.alias }}
        {% else %}
            LEFT JOIN {{ config.table }} AS {{ config.alias }} 
                ON {{ config.join_condition }}
        {% endif %}
    {% endfor %}