SELECT cast(floor(mid_lon / 0.0015) AS bigint) AS cx, cast(floor(mid_lat / 0.0015) AS bigint) AS cy,
       avg(heat_index) AS heat, sum(length_m) AS length_m
FROM coolwalk.segments GROUP BY 1, 2
