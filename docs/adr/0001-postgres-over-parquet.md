# PostgreSQL over Parquet for OHLCV storage

For a single-user experimentation CLI, Parquet files would be simpler — zero infrastructure, native pandas integration, no ORM boilerplate. We chose PostgreSQL instead because a primary goal of this project is demonstrating industry-standard technologies in a real-world context (portfolio piece). The operational overhead (running Postgres, connection management, Alembic migrations) is accepted as a trade-off for demonstrability. The database also enables the multi-user architecture where a centralized Lambda syncs data and users have read-only access.

## Considered Options

- **Parquet files** — simpler, zero infrastructure, native pandas I/O. Rejected because it doesn't showcase database skills.
- **SQLite** — middle ground, file-based but SQL-capable. Rejected because it doesn't represent production database usage.
