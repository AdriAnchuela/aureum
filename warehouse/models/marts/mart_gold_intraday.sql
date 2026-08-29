-- 1-minute OHLC bars from the PAXG tick stream: gold's 24/7 pulse,
-- alive even when COMEX sleeps (weekends — when geopolitical shocks land).
select
    date_trunc('minute', ts_exchange)  as minute,
    arg_min(price, ts_exchange)        as open,
    max(price)                         as high,
    min(price)                         as low,
    arg_max(price, ts_exchange)        as close,
    sum(qty)                           as volume,
    count(*)                           as n_trades
from {{ ref('stg_paxg_trades') }}
group by 1
order by 1
