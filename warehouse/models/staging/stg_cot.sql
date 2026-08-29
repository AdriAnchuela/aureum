select
    report_date,
    instrument,
    open_interest,
    noncomm_long,
    noncomm_short,
    net_noncommercial,
    net_commercial
from read_parquet('{{ var("lake_path") }}/raw/cot/legacy_futures/latest.parquet')
