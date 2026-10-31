# Tableau calculated fields for `ontime_extract_2025.csv`

Connect Tableau (Desktop or Public) to the CSV as a text source, then add:

| Name | Formula |
|---|---|
| OTP % | `SUM([on_time]) / SUM([operated])` (format as percentage) |
| Cancel rate % | `SUM([cancelled]) / SUM([scheduled_flights])` |
| Delay minutes per operated flight | `SUM([delay_minutes]) / SUM([operated])` |
| OTP vs network | `[OTP %] - WINDOW_SUM(SUM([on_time])) / WINDOW_SUM(SUM([operated]))` (table calc, across all) |
| Carrier rank | `RANK([OTP %])` (compute by carrier_name) |

Suggested sheets: monthly OTP line (month), carrier bar (carrier_name, sorted by OTP %), airport map or bar (origin), carrier x airport heatmap of OTP vs network.
The extract only covers the 30 busiest origin airports, so its totals are lower than the network totals in `reports/kpis.json`.
