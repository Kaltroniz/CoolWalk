SELECT round(sum(CASE WHEN heat_index >= 0.66 THEN length_m ELSE 0 END) / sum(length_m), 4) AS hot_share,
       round(sum(length_m) / 2000, 1) AS network_km,
       round(approx_percentile(lst_c, 0.05), 1) AS lst_p05_c,
       round(approx_percentile(lst_c, 0.95), 1) AS lst_p95_c
FROM coolwalk.segments;
