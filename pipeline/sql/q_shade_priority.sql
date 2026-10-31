SELECT
  s.name AS corridor,
  round(avg(s.lst_c), 1) AS avg_surface_c,
  round(avg(s.heat_index), 2) AS avg_heat_index,
  round(sum(s.length_m) / 2) AS total_hot_m,
  count(distinct case when p.kind = 'bus_stop' then p.place_id end) AS bus_stops,
  count(distinct case when p.kind = 'school' then p.place_id end) AS schools,
  count(distinct case when p.kind = 'hospital' then p.place_id end) AS hospitals,
  round(arbitrary(s.mid_lon), 5) AS lon,
  round(arbitrary(s.mid_lat), 5) AS lat
FROM coolwalk.segments s
JOIN coolwalk.places p
  ON p.kind IN ('bus_stop', 'school', 'hospital')
 AND abs(s.mid_lat - p.lat) <= 0.0013
 AND abs(s.mid_lon - p.lon) <= 0.0015
 AND sqrt(power((s.mid_lon - p.lon) * 111320.0 * 0.878, 2) + power((s.mid_lat - p.lat) * 110540.0, 2)) <= 150.0
WHERE s.name IS NOT NULL AND s.name != '' AND s.heat_index >= 0.66
GROUP BY s.name
HAVING count(distinct case when p.kind IN ('bus_stop', 'school', 'hospital') then p.place_id end) > 0
ORDER BY (count(distinct case when p.kind = 'school' then p.place_id end) * 3 +
          count(distinct case when p.kind = 'hospital' then p.place_id end) * 3 +
          count(distinct case when p.kind = 'bus_stop' then p.place_id end) * 2) DESC,
         total_hot_m DESC
LIMIT 20;
