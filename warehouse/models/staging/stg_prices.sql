-- Latest snapshot of daily OHLC from Stooq (one line = the lake contract).
select date, symbol, name, open, high, low, close
from read_parquet('{{ var("lake_path") }}/raw/prices/daily/latest.parquet')
