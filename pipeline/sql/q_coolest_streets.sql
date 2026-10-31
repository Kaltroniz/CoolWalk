SELECT name, round(avg(heat_index), 3) AS heat, round(sum(length_m)) AS length_m,
       round(avg(lst_c), 1) AS lst_c, round(approx_percentile(mid_lon, 0.5), 5) AS lon, round(approx_percentile(mid_lat, 0.5), 5) AS lat
FROM coolwalk.segments
WHERE name IS NOT NULL AND name <> '' AND highway IN ('primary','secondary','tertiary','residential','unclassified','pedestrian','living_street')
GROUP BY name HAVING sum(length_m) > 500
ORDER BY heat ASC LIMIT 8;
