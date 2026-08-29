select
    event_id,
    strptime(event_date, '%Y%m%d')::date as event_date,
    event_root_code,
    quad_class,
    goldstein,
    num_articles,
    avg_tone,
    action_country
from read_parquet('{{ var("lake_path") }}/raw/gdelt/events/date=*/*.parquet')
