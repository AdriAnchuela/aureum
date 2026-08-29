-- One row per macro prediction market: the leading outcome and its odds.
select
    market_id,
    question,
    arg_max(outcome, implied_prob)  as leading_outcome,
    max(implied_prob)               as leading_prob,
    max(volume_24h)                 as volume_24h,
    max(end_date)                   as end_date
from {{ ref('stg_polymarket_odds') }}
group by market_id, question
order by volume_24h desc
