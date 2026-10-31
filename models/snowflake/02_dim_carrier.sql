SELECT c.code AS carrier_code, c.description AS carrier_name
FROM raw_carriers c
WHERE c.code IN (SELECT DISTINCT carrier_code FROM stg_flights)
QUALIFY ROW_NUMBER() OVER (PARTITION BY c.code ORDER BY c.description) = 1
