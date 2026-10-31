"""Build pipeline: Snowflake-dialect SQL models -> sqlglot transpile -> DuckDB, then KPIs, charts, README."""
import json, pathlib, sys
import duckdb, sqlglot

ROOT = pathlib.Path(__file__).parent
MODELS = sorted((ROOT / "models/snowflake").glob("*.sql"))

def model_name(p):
    return p.stem.split("_", 1)[1]

def to_duckdb(sql: str) -> str:
    return sqlglot.transpile(sql, read="snowflake", write="duckdb")[0]

def build(con):
    for p in MODELS:
        sql = to_duckdb(p.read_text())
        con.execute(f"CREATE OR REPLACE TABLE {model_name(p)} AS {sql}")

def load_raw(con, parquet_glob, carriers_csv):
    con.execute(f"CREATE OR REPLACE VIEW raw_ontime AS SELECT * FROM read_parquet('{parquet_glob}')")
    con.execute(f"CREATE OR REPLACE TABLE raw_carriers AS SELECT \"Code\" AS code, \"Description\" AS description FROM read_csv('{carriers_csv}', header=true, all_varchar=true)")

def kpis(con):
    q = lambda s: con.execute(s).fetchone()
    tot = q("""SELECT SUM(scheduled_flights), SUM(cancelled), SUM(operated), SUM(on_time),
               SUM(carrier_delay_min), SUM(weather_delay_min), SUM(nas_delay_min),
               SUM(security_delay_min), SUM(late_aircraft_delay_min) FROM fct_carrier_month""")
    k = {"flights": int(tot[0]), "cancelled": int(tot[1]), "otp_pct": round(100 * tot[3] / tot[2], 1),
         "cancel_rate_pct": round(100 * tot[1] / tot[0], 2)}
    causes = dict(zip(["carrier", "weather", "nas", "security", "late_aircraft"], tot[4:]))
    tc = sum(causes.values())
    k["delay_cause_share_pct"] = {c: round(100 * v / tc, 1) for c, v in causes.items()}
    car = con.execute("""SELECT d.carrier_name, SUM(on_time)/SUM(operated) otp, SUM(scheduled_flights) n
        FROM fct_carrier_month f JOIN dim_carrier d USING (carrier_code) GROUP BY 1 ORDER BY otp DESC, 1""").fetchall()
    k["carriers"] = len(car)
    k["best_carrier"] = {"name": car[0][0], "otp_pct": round(100 * car[0][1], 1)}
    k["worst_carrier"] = {"name": car[-1][0], "otp_pct": round(100 * car[-1][1], 1)}
    m = con.execute("SELECT strftime(month,'%Y-%m'), SUM(on_time)/SUM(operated) FROM fct_carrier_month GROUP BY 1 ORDER BY 2").fetchall()
    k["worst_month"] = {"month": m[0][0], "otp_pct": round(100 * m[0][1], 1)}
    k["best_month"] = {"month": m[-1][0], "otp_pct": round(100 * m[-1][1], 1)}
    h = dict(con.execute("SELECT sched_dep_hour, otp FROM fct_hour WHERE scheduled_flights > 10000").fetchall())
    k["otp_6am_pct"] = round(100 * h[6], 1)
    k["otp_worst_hour"] = {"hour": max(h, key=lambda x: -h[x]), "otp_pct": round(100 * min(h.values()), 1)}
    a = con.execute("SELECT origin, otp FROM fct_airport ORDER BY otp DESC, origin").fetchall()
    k["best_airport"] = {"code": a[0][0], "otp_pct": round(100 * a[0][1], 1)}
    k["worst_airport"] = {"code": a[-1][0], "otp_pct": round(100 * a[-1][1], 1)}
    return k

def main():
    import charts, readme
    con = duckdb.connect(str(ROOT / "data/warehouse.duckdb"))
    load_raw(con, str(ROOT / "data/parquet/*.parquet"), str(ROOT / "data/raw/L_UNIQUE_CARRIERS.csv"))
    build(con)
    k = kpis(con)
    (ROOT / "reports/kpis.json").write_text(json.dumps(k, indent=1))
    con.execute(f"COPY tableau_extract TO '{ROOT}/tableau/ontime_extract_2025.csv' (HEADER)")
    for t in ["fct_carrier_month", "fct_airport", "fct_hour", "dim_carrier"]:
        con.execute(f"COPY (SELECT * FROM {t} ORDER BY ALL) TO '{ROOT}/reports/{t}.csv' (HEADER)")
    charts.render(con, k)
    readme.write(k)
    print(json.dumps(k, indent=1))

if __name__ == "__main__":
    sys.path.insert(0, str(ROOT)); main()
