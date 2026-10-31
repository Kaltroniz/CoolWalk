SELECT name, round(avg(heat_index), 3) AS heat, round(sum(length_m) / 2) AS length_m,
       round(avg(lst_c), 1) AS lst_c, round(max_by(mid_lon, length_m), 5) AS lon, round(max_by(mid_lat, length_m), 5) AS lat
FROM coolwalk.segments
WHERE name IS NOT NULL AND name <> '' AND highway IN ('primary','secondary','tertiary','residential','unclassified','pedestrian','living_street')
GROUP BY name HAVING sum(length_m) > 500
ORDER BY heat ASC LIMIT 8;
