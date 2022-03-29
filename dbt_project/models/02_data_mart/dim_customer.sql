select
     raw_customer.C_CUSTKEY  as cust_key
    ,raw_customer.C_NAME     as full_name
    ,raw_nation.N_NAME     as nation_name
from {{ref('raw_customer')}} as raw_customer

left join {{ref('raw_nation')}} as raw_nation
    on raw_customer.C_NATIONKEY = raw_nation.N_NATIONKEY
