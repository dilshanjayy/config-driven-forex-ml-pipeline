# Composite primary key for ohlcv table

An OHLCV row is uniquely identified by its (pair, interval, timestamp) — that's the natural key, and the only key any query ever uses. We use this composite key as the primary key instead of a surrogate `BIGSERIAL id` column. This eliminates a column nothing references, removes a redundant index (Postgres creates a B-tree on the PK automatically, so the separate `UNIQUE` constraint and explicit index are no longer needed), and simplifies upserts (`ON CONFLICT` targets the PK directly).

## Considered Options

- **Surrogate `id BIGSERIAL PRIMARY KEY`** with a separate `UNIQUE(pair, interval, timestamp)` — conventional, simplifies foreign keys if other tables ever reference individual rows. Rejected because no table in v1 references `ohlcv` rows, the `id` column would leak into DataFrames requiring explicit exclusion, and it creates a redundant index.
