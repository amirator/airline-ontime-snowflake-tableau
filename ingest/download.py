"""Download BTS Reporting Carrier On-Time Performance files (calendar 2025) and the
carrier lookup, record a manifest, and convert each month to Parquet (selected columns)."""
import hashlib, json, pathlib, subprocess, sys, zipfile, datetime as dt
import duckdb, requests

RAW = pathlib.Path("data/raw"); PQ = pathlib.Path("data/parquet")
BASE = "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip"
LOOKUP = "https://transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_haVdhR_PNeeVRef"  # L_UNIQUE_CARRIERS
COLS = ["FlightDate", "Reporting_Airline", "Origin", "Dest", "CRSDepTime", "DepDelay", "ArrDelay",
        "ArrDel15", "Cancelled", "CancellationCode", "Diverted", "Distance", "CarrierDelay",
        "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay"]

def sha(p):
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def main(year=2025, months=range(1, 13)):
    RAW.mkdir(parents=True, exist_ok=True); PQ.mkdir(parents=True, exist_ok=True)
    manifest = []
    for m in months:
        z = RAW / f"ot_{year}_{m}.zip"; url = BASE.format(y=year, m=m)
        if not z.exists():
            r = requests.get(url, timeout=600); r.raise_for_status(); z.write_bytes(r.content)
        manifest.append({"url": url, "file": z.name, "bytes": z.stat().st_size, "sha256": sha(z)})
        out = PQ / f"ot_{year}_{m:02d}.parquet"
        if not out.exists():
            with zipfile.ZipFile(z) as zf:
                name = [n for n in zf.namelist() if n.endswith(".csv")][0]
                zf.extract(name, RAW); csv = RAW / name
            cols = ", ".join(f'"{c}"' for c in COLS)
            duckdb.sql(f"COPY (SELECT {cols} FROM read_csv('{csv}', header=true, all_varchar=true)) TO '{out}' (FORMAT parquet)")
            csv.unlink()
    lk = RAW / "L_UNIQUE_CARRIERS.csv"
    if not lk.exists():
        r = requests.get(LOOKUP, timeout=120); r.raise_for_status(); lk.write_bytes(r.content)
    manifest.append({"url": LOOKUP, "file": lk.name, "bytes": lk.stat().st_size, "sha256": sha(lk)})
    pathlib.Path("data/manifest.json").write_text(json.dumps(
        {"downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "files": manifest}, indent=1))

if __name__ == "__main__":
    main()
