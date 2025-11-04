# ETL - Data Loading and Processing

Scripts for extracting, transforming, and loading data from various sources into the dashboard database.

## Features

- Load CSV/Excel data
- Data validation and quality checks
- Automatic error handling and logging
- Support for multiple data sources
- Batch processing for performance

## Files

- `load_csv_data.py` - Main ETL script to load initial reference data
- `requirements.txt` - Python dependencies

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/dashboard_db"
   ```

## Usage

### Load initial data

```bash
python load_csv_data.py
```

This will:
1. Load all municipal organizations (МО)
2. Create monthly periods
3. Load indicators and their metadata
4. Create methodology version
5. Register data sources

### Output

```
2024-11-04 12:00:00 - INFO - Starting data load...
2024-11-04 12:00:00 - INFO - Loading municipal organizations...
2024-11-04 12:00:01 - INFO - Added MO: Липецк
...
2024-11-04 12:00:05 - INFO - Data load completed successfully!
```

## Data Flow

```
Raw CSV/Excel Files
        ↓
   Parse & Validate
        ↓
   Transform Data
        ↓
   Load to Database
        ↓
    Calculate Metrics
        ↓
   Audit & Quality Checks
```

## Supported Data Formats

- CSV (comma-separated)
- Excel (.xlsx)
- JSON (future)

## Error Handling

All errors are:
- Logged with timestamp and details
- Rolled back to previous state
- Reported with actionable messages

## Performance

- Batch size: 1000 records
- Connection pooling enabled
- Indexes created for fast queries
- Transaction support

## Development

### Add new ETL script

1. Create `load_<source>.py` in this directory
2. Inherit from base ETLLoader class (to be created)
3. Implement `parse()` and `load()` methods
4. Add to `__main__` runner

### Testing

```bash
pytest tests/ -v
```

## Scheduling

For production, use:
- **Airflow** for orchestration
- **Prefect** as alternative
- **cron** for simple scheduled tasks

Example cron job:
```cron
0 6 * * * cd /app && python etl/load_csv_data.py >> /var/log/etl.log 2>&1
```

## Logging

Logs are written to:
- Console (INFO level)
- File (to be configured): `/var/log/dashboard/etl.log`

## Troubleshooting

### Connection timeout
```bash
# Check database is running
docker-compose logs postgres
docker-compose exec postgres psql -U dashboard_user -d dashboard_db -c "SELECT 1"
```

### Data validation errors
- Check CSV format matches expected schema
- Verify encodings (UTF-8)
- Validate data ranges

### Memory issues
- Reduce batch_size in config
- Process files in chunks
- Monitor with `docker stats`

## Future Enhancements

- [ ] API-based data ingestion
- [ ] Real-time streaming
- [ ] Data reconciliation reports
- [ ] Automated quality score calculation
- [ ] Change data capture (CDC)
- [ ] Incremental loads

## Related Documentation

- [Database Schema](../database_schema.sql)
- [Backend API](../backend/README.md)
- [Main README](../README.md)
