WITH hot AS (
  SELECT name, length_m, lst_c, heat_index, mid_lon, mid_lat
  FROM coolwalk.segments
  WHERE heat_index >= 0.66 AND name IS NOT NULL AND name <> ''),
st AS (
  SELECT name, round(avg(lst_c), 1) AS avg_surface_c, round(avg(heat_index), 2) AS avg_heat_index,
         round(sum(length_m) / 2) AS total_hot_m,
         round(max_by(mid_lon, length_m), 5) AS lon, round(max_by(mid_lat, length_m), 5) AS lat
  FROM hot GROUP BY name),
near AS (
  SELECT DISTINCT h.name, p.place_id, p.kind
  FROM hot h JOIN coolwalk.places p
    ON p.kind IN ('bus_stop', 'school', 'hospital')
   AND abs(h.mid_lat - p.lat) <= 0.0013 AND abs(h.mid_lon - p.lon) <= 0.0015
   AND sqrt(power((h.mid_lon - p.lon) * 111320.0 * 0.878, 2) + power((h.mid_lat - p.lat) * 110540.0, 2)) <= 150.0),
pc AS (
  SELECT name,
         count(CASE WHEN kind = 'bus_stop' THEN 1 END) AS bus_stops,
         count(CASE WHEN kind = 'school' THEN 1 END) AS schools,
         count(CASE WHEN kind = 'hospital' THEN 1 END) AS hospitals
  FROM near GROUP BY name)
SELECT st.name AS corridor, st.avg_surface_c, st.avg_heat_index, st.total_hot_m,
       pc.bus_stops, pc.schools, pc.hospitals, st.lon, st.lat
FROM st JOIN pc ON st.name = pc.name
ORDER BY (pc.schools * 3 + pc.hospitals * 3 + pc.bus_stops * 2) DESC, st.total_hot_m DESC
LIMIT 20;
