select
    fetched_at,
    market_id,
    question,
    slug,
    outcome,
    implied_prob,
    token_id,
    volume_24h,
    liquidity,
    try_cast(end_date as timestamp) as end_date
from read_parquet('{{ var("lake_path") }}/raw/polymarket/macro_odds/latest.parquet')
