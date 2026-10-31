-- Tableau-ready monthly extract (one row per month x carrier x origin for the 30 busiest airports).
SELECT DATE_TRUNC('MONTH', f.flight_date) AS month, f.carrier_code, d.carrier_name, f.origin,
       COUNT(*) AS scheduled_flights, SUM(f.is_cancelled) AS cancelled,
       SUM(IFF(f.is_cancelled = 0 AND f.is_diverted = 0, 1, 0)) AS operated,
       SUM(IFF(f.is_cancelled = 0 AND f.is_diverted = 0 AND f.is_arr_late15 = 0, 1, 0)) AS on_time,
       ROUND(SUM(f.carrier_delay_min + f.weather_delay_min + f.nas_delay_min + f.security_delay_min + f.late_aircraft_delay_min)) AS delay_minutes
FROM stg_flights f
JOIN dim_carrier d USING (carrier_code)
WHERE f.origin IN (SELECT origin FROM fct_airport)
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 4
