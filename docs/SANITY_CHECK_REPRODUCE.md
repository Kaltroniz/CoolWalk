# Reproducible Sanity Check: Leafy vs Dense Streets

This document provides the exact Athena SQL query and Python inspection script to reproduce the street-level temperature, vegetation, and heat index numbers cited in `docs/FINDINGS.md` and `docs/WRITEUP.md`.

## 1. Athena SQL Query

Execute in the Amazon Athena console or via `boto3`:

```sql
SELECT
  name,
  count(*) AS segment_count,
  round(avg(lst_c), 1) AS mean_lst_c,
  round(min(lst_c), 1) AS min_lst_c,
  round(max(lst_c), 1) AS max_lst_c,
  round(avg(ndvi), 3) AS mean_ndvi,
  round(avg(heat_index), 3) AS mean_heat_index,
  round(sum(length_m), 1) AS total_length_m
FROM coolwalk.segments
WHERE name IN (
  'Akbar Road', 'Teen Murti Marg', 'Janpath Lane', 'Janpath',
  'Lal Kuan Bazar', 'Khari Baoli Road', 'Chandni Chowk', 'Nai Sarak',
  'Chawri Bazar', 'Kinari Bazar', 'Chipwara Khurd'
)
GROUP BY name
ORDER BY mean_heat_index ASC;
```

## 2. Python / Parquet Verification Command

Run directly against the local scored dataset:

```bash
python -c "
import pandas as pd
df = pd.read_parquet('work/segments.parquet')
streets = [
    'Akbar Road', 'Teen Murti Marg', 'Janpath Lane', 'Janpath',
    'Lal Kuan Bazar', 'Khari Baoli Road', 'Chandni Chowk', 'Nai Sarak',
    'Chawri Bazar', 'Kinari Bazar', 'Chipwara Khurd'
]
grp = df[df.name.isin(streets)].groupby('name').agg(
    segments=('edge_id', 'count'),
    mean_lst=('lst_c', 'mean'),
    min_lst=('lst_c', 'min'),
    max_lst=('lst_c', 'max'),
    mean_ndvi=('ndvi', 'mean'),
    mean_heat=('heat_index', 'mean')
).loc[streets]
print(grp.round({'mean_lst': 1, 'min_lst': 1, 'max_lst': 1, 'mean_ndvi': 3, 'mean_heat': 3}))
"
```

## 3. Verified Output Table

| Street Name | Classification | Segments | Mean LST (°C) | Measured LST Range (°C) | Mean NDVI | Mean Heat Index (0..1) | Context |
|---|---|---|---|---|---|---|---|
| **Akbar Road** | secondary | 56 | 40.6 | 39.3–41.9 | 0.961 | 0.042 | Dense canopy avenue in Lutyens' Delhi |
| **Teen Murti Marg** | secondary | 30 | 41.0 | 40.2–42.5 | 0.954 | 0.068 | Forested boulevard near Teen Murti |
| **Janpath Lane** | tertiary | 20 | 42.2 | 41.6–43.6 | 0.935 | 0.192 | Tree-lined access lane near Janpath |
| **Janpath** | secondary | 180 | 42.5 | 39.7–44.1 | 0.755 | 0.252 | Wide commercial and diplomatic avenue |
| **Lal Kuan Bazar** | tertiary | 28 | 45.6 | 44.6–46.4 | 0.229 | 0.776 | Dense commercial corridor in Old Delhi |
| **Khari Baoli Road** | tertiary | 12 | 46.4 | 45.6–47.0 | 0.365 | 0.741 | Historic wholesale spice market |
| **Chandni Chowk** | tertiary | 84 | 46.2 | 45.2–46.8 | 0.349 | 0.754 | Primary commercial thoroughfare |
| **Nai Sarak** | unclassified | 22 | 46.4 | 46.0–46.8 | 0.188 | 0.868 | Dense book market corridor |
| **Chawri Bazar** | tertiary | 24 | 46.3 | 45.4–46.7 | 0.169 | 0.871 | High-density metal market street |
| **Kinari Bazar** | unclassified | 18 | 46.2 | 45.9–46.5 | 0.115 | 0.914 | High-density jewelry alley in Shahjahanabad |
| **Chipwara Khurd** | unclassified | 12 | 46.1 | 46.0–46.2 | 0.072 | 0.934 | Narrow residential/commercial alley |
