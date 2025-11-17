# Data Loading Instructions - Official Methodology

## Summary

Данные из CSV файлов были проанализированы и маппированы на официальные коды критериев. Создан готовый SQL скрипт для загрузки данных в БД.

## What You Need to Do

### 1. Run SQL Script on Amvera PostgreSQL

The file `load_official_data.sql` contains all INSERT statements to populate the `fact_indicator` table with data from your CSV files.

**Steps:**

1. Connect to Amvera PostgreSQL database (using pgAdmin, DBeaver, or psql)
2. Open the file: `load_official_data.sql` from your repository
3. Copy entire contents and paste into SQL query editor
4. Execute the SQL script

### 2. Expected Result

The script will insert data for 18 criteria:
- ПУБЛИЧНЫЙ (PUBLIC): 7 criteria out of 9
- ЗАКРЫТЫЙ (CLOSED): 7 criteria out of 8
- PENALTIES: 3 criteria

All 20 municipalities will have scores loaded.

### 3. Verify the Load

After executing, run this verification query:

```sql
SELECT code, COUNT(*) as records_count
FROM dim_indicator i
JOIN fact_indicator f ON i.ind_id = f.ind_id
WHERE f.period_id = 1
GROUP BY code
ORDER BY code;
```

You should see 18 criteria with 20 records each.

### 4. Refresh Frontend

After data is loaded:
1. Navigate to Rating tab in the frontend
2. Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)
3. Scores should now display instead of zeros

## Data Mapping Summary

All CSV data has been mapped to official criteria codes:
- pub_2 to pub_9 (7 PUBLIC criteria loaded)
- closed_1 to closed_5, closed_7 to closed_8 (7 CLOSED criteria loaded)
- pen_1, pen_2, pen_3 (3 PENALTY criteria loaded)

Missing:
- pub_1 (no CSV data for "Поддержка руководства")
- closed_6 (no CSV data for "Работа с ветеранами закрыто")

## File References

- SQL Script: `load_official_data.sql` - ready to execute
- Analysis: `load_data_simple.py` - shows data validation
- Docs: `OFFICIAL_METHODOLOGY_*.md` files
