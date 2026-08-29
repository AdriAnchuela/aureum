-- Daily aggregation of the GDELT firehose: raw material for the phase-3
-- geopolitical risk index. conflict_share weights events by press coverage.
select
    event_date,
    count(*)                                   as n_events,
    avg(goldstein)                             as avg_goldstein,
    avg(avg_tone)                              as avg_tone,
    sum(num_articles) filter (quad_class in (3, 4))::double
        / nullif(sum(num_articles), 0)         as conflict_article_share
from {{ ref('stg_gdelt_events') }}
group by event_date
order by event_date
