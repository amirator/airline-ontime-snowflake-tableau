SELECT sched_dep_hour,
       COUNT(*) AS scheduled_flights,
       DIV0(SUM(IFF(is_cancelled = 0 AND is_diverted = 0 AND is_arr_late15 = 0, 1, 0)),
            SUM(IFF(is_cancelled = 0 AND is_diverted = 0, 1, 0))) AS otp,
       AVG(IFF(is_cancelled = 0 AND is_diverted = 0, arr_delay_min, NULL)) AS avg_arr_delay_min
FROM stg_flights
WHERE sched_dep_hour BETWEEN 0 AND 23
GROUP BY sched_dep_hour
