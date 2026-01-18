# medical_warehouse/

dbt project for transforming raw Telegram data into a star schema.

## Status

✅ **All models built and tested** (39/39 tests passing)

## Star Schema

**Staging:**
- `stg_telegram_messages` - Cleaned and typed raw data (17 rows)

**Dimensions:**
- `dim_channels` - Channel statistics (3 channels)
- `dim_dates` - Date dimension (2,574 dates, 2020-2027)

**Fact:**
- `fct_messages` - Message-level data with engagement metrics (17 rows)

## Commands

```bash
# Build all models
./scripts/run_dbt.sh run

# Run tests (39 tests)
./scripts/run_dbt.sh test

# Generate documentation
./scripts/run_dbt.sh docs generate
./scripts/run_dbt.sh docs serve  # View at http://localhost:8080
```

## Models

- **Staging**: Views for cleaning and standardization
- **Marts**: Tables for dimensional model (star schema)

## Tests

- Unique/Not Null: Primary keys and critical fields
- Relationships: Foreign key integrity
- Accepted Values: Enum-like fields
- Custom: Business logic validation (no future dates, positive metrics, valid names)
