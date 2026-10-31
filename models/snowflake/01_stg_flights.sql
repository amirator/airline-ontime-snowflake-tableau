-- Staging: typed flight-level rows. Written in Snowflake SQL; transpiled to DuckDB by run.py.
SELECT
  TRY_CAST(FlightDate AS DATE)                         AS flight_date,
  Reporting_Airline                               AS carrier_code,
  Origin                                          AS origin,
  Dest                                            AS dest,
  TRY_CAST(SUBSTR(CRSDepTime, 1, 2) AS INTEGER)         AS sched_dep_hour,
  TRY_CAST(ArrDelay AS DOUBLE)                         AS arr_delay_min,
  TRY_CAST(DepDelay AS DOUBLE)                         AS dep_delay_min,
  IFF(TRY_CAST(Cancelled AS DOUBLE) = 1, 1, 0)         AS is_cancelled,
  IFF(TRY_CAST(Diverted AS DOUBLE) = 1, 1, 0)          AS is_diverted,
  NULLIF(CancellationCode, '')                    AS cancel_code,
  IFF(TRY_CAST(ArrDel15 AS DOUBLE) = 1, 1, 0)          AS is_arr_late15,
  TRY_CAST(Distance AS DOUBLE)                         AS distance_mi,
  COALESCE(TRY_CAST(CarrierDelay AS DOUBLE), 0)        AS carrier_delay_min,
  COALESCE(TRY_CAST(WeatherDelay AS DOUBLE), 0)        AS weather_delay_min,
  COALESCE(TRY_CAST(NASDelay AS DOUBLE), 0)            AS nas_delay_min,
  COALESCE(TRY_CAST(SecurityDelay AS DOUBLE), 0)       AS security_delay_min,
  COALESCE(TRY_CAST(LateAircraftDelay AS DOUBLE), 0)   AS late_aircraft_delay_min
FROM raw_ontime
