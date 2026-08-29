-- One row per trading day: gold against the macro forces that move it.
with gold as (
    select date, close as gold_usd
    from {{ ref('stg_prices') }}
    where symbol = 'GC=F'
),

macro as (
    select
        date,
        max(value) filter (series_id = 'DFII10')   as real_yield_10y,
        max(value) filter (series_id = 'DGS10')    as nominal_yield_10y,
        max(value) filter (series_id = 'T10Y2Y')   as curve_10y_2y,
        max(value) filter (series_id = 'DTWEXBGS') as usd_broad_index,
        max(value) filter (series_id = 'VIXCLS')   as vix
    from {{ ref('stg_fred') }}
    group by date
)

select
    gold.date,
    gold.gold_usd,
    gold.gold_usd / lag(gold.gold_usd) over (order by gold.date) - 1 as gold_return_1d,
    macro.real_yield_10y,
    macro.nominal_yield_10y,
    macro.curve_10y_2y,
    macro.usd_broad_index,
    macro.vix
from gold
left join macro using (date)
order by gold.date
