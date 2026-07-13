# Centralized data sync via Lambda instead of user-facing CLI

Data syncing (TwelveData API → PostgreSQL) is handled by a centralized AWS Lambda running daily on a schedule, rather than being a user-facing CLI command. Users have read-only database access and cannot write OHLCV data. The `fxml sync` CLI command is retained as a dev/admin tool that reuses the same sync module code. The Lambda reads its list of pairs and intervals from a config file in S3.

This architecture enforces least-privilege access in a multi-user setup and demonstrates cloud engineering skills (Lambda, S3, IAM, CloudWatch scheduling). The trade-off is additional infrastructure complexity (Terraform, Lambda packaging) for what could be a simple CLI command in a single-user tool.
