-- Origin-airport OTP with a rank over the 30 busiest airports.
WITH a AS (
  SELECT origin,
         COUNT(*) AS scheduled_flights,
         SUM(IFF(is_cancelled = 0 AND is_diverted = 0, 1, 0)) AS operated,
         DIV0(SUM(IFF(is_cancelled = 0 AND is_diverted = 0 AND is_arr_late15 = 0, 1, 0)),
              SUM(IFF(is_cancelled = 0 AND is_diverted = 0, 1, 0))) AS otp,
         DIV0(SUM(is_cancelled), COUNT(*)) AS cancel_rate
  FROM stg_flights GROUP BY origin
)
SELECT *, RANK() OVER (ORDER BY otp DESC) AS otp_rank_top30
FROM a
QUALIFY ROW_NUMBER() OVER (ORDER BY scheduled_flights DESC, origin) <= 30
