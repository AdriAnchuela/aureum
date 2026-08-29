select date, series_id, name, value
from read_parquet('{{ var("lake_path") }}/raw/fred/series/latest.parquet')
