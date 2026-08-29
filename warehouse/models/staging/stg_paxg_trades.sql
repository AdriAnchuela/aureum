select ts_exchange, trade_id, price, qty, buyer_is_maker
from read_parquet('{{ var("lake_path") }}/raw/paxg/trades/date=*/*.parquet')
