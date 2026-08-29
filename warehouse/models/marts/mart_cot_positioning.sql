-- Weekly speculative positioning with a 3-year z-score: "are the large specs
-- unusually long gold right now?" — the divergence input for phase-3 anomalies.
with base as (
    select
        report_date,
        instrument,
        open_interest,
        net_noncommercial,
        net_noncommercial::double / nullif(open_interest, 0) as net_share_oi
    from {{ ref('stg_cot') }}
)

select
    *,
    (net_noncommercial - avg(net_noncommercial) over w)
        / nullif(stddev(net_noncommercial) over w, 0) as positioning_zscore_3y
from base
window w as (
    partition by instrument
    order by report_date
    rows between 155 preceding and current row
)
order by instrument, report_date
