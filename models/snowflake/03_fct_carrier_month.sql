-- On-time performance (OTP) = share of operated (not cancelled/diverted) flights arriving < 15 min late.
SELECT
  DATE_TRUNC('MONTH', flight_date)                                   AS month,
  carrier_code,
  COUNT(*)                                                           AS scheduled_flights,
  SUM(is_cancelled)                                                  AS cancelled,
  SUM(is_diverted)                                                   AS diverted,
  SUM(IFF(is_cancelled = 0 AND is_diverted = 0, 1, 0))               AS operated,
  SUM(IFF(is_cancelled = 0 AND is_diverted = 0 AND is_arr_late15 = 0, 1, 0)) AS on_time,
  DIV0(SUM(IFF(is_cancelled = 0 AND is_diverted = 0 AND is_arr_late15 = 0, 1, 0)),
       SUM(IFF(is_cancelled = 0 AND is_diverted = 0, 1, 0)))         AS otp,
  DIV0(SUM(is_cancelled), COUNT(*))                                  AS cancel_rate,
  SUM(carrier_delay_min)       AS carrier_delay_min,
  SUM(weather_delay_min)       AS weather_delay_min,
  SUM(nas_delay_min)           AS nas_delay_min,
  SUM(security_delay_min)      AS security_delay_min,
  SUM(late_aircraft_delay_min) AS late_aircraft_delay_min
FROM stg_flights
GROUP BY 1, 2
