select * from {{ source('snowflake_sample','customer') }}
where C_CUSTKEY >= {{ var('load_custkey_limit') }}
limit 100
