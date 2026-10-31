import json, pathlib, sys
import duckdb, pytest, sqlglot
ROOT = pathlib.Path(__file__).parents[1]; sys.path.insert(0, str(ROOT))
import run

FIXTURE = [  # hand-made unit-test rows (not real data) covering on-time, late, cancelled, diverted
    ("2025-01-05", "AA", "JFK", "LAX", "0659", "-3", "-7", "0", "0", "", "0", "2475", "", "", "", "", ""),
    ("2025-01-05", "AA", "JFK", "LAX", "1800", "40", "45", "1", "0", "", "0", "2475", "10", "0", "5", "0", "30"),
    ("2025-01-06", "DL", "ATL", "JFK", "0700", "", "", "", "1", "B", "0", "760", "", "", "", "", ""),
    ("2025-02-01", "DL", "ATL", "JFK", "0700", "5", "", "", "0", "", "1", "760", "", "", "", "", ""),
]

@pytest.fixture
def con(tmp_path):
    c = duckdb.connect()
    cols = ", ".join(f'"{x}" VARCHAR' for x in ["FlightDate","Reporting_Airline","Origin","Dest","CRSDepTime","DepDelay","ArrDelay","ArrDel15","Cancelled","CancellationCode","Diverted","Distance","CarrierDelay","WeatherDelay","NASDelay","SecurityDelay","LateAircraftDelay"])
    c.execute(f"CREATE TABLE raw_ontime ({cols})")
    c.executemany(f"INSERT INTO raw_ontime VALUES ({','.join('?'*17)})", FIXTURE)
    c.execute("CREATE TABLE raw_carriers AS SELECT * FROM (VALUES ('AA','American Airlines Inc.'),('DL','Delta Air Lines Inc.'),('ZZ','Unused')) t(code, description)")
    run.build(c); return c

def test_every_model_transpiles_and_parses_as_snowflake():
    for p in run.MODELS:
        sqlglot.parse_one(p.read_text(), read="snowflake")
        assert "TRY_TO_" not in run.to_duckdb(p.read_text()).upper()

def test_otp_definition(con):
    r = con.execute("SELECT SUM(scheduled_flights), SUM(cancelled), SUM(diverted), SUM(operated), SUM(on_time) FROM fct_carrier_month").fetchone()
    assert r == (4, 1, 1, 2, 1)

def test_dim_carrier_only_used_codes(con):
    assert sorted(x[0] for x in con.execute("SELECT carrier_code FROM dim_carrier").fetchall()) == ["AA", "DL"]

def test_delay_causes_sum(con):
    r = con.execute("SELECT SUM(carrier_delay_min + nas_delay_min + late_aircraft_delay_min) FROM fct_carrier_month").fetchone()[0]
    assert r == 45

def test_div0_no_error(con):
    r = con.execute("SELECT otp FROM fct_carrier_month WHERE carrier_code='DL' AND month='2025-02-01'").fetchone()[0]
    assert r == 0

def test_readme_matches_kpis():
    k = json.loads((ROOT / "reports/kpis.json").read_text()); md = (ROOT / "README.md").read_text()
    for v in [f"{k['flights']:,}", f"{k['otp_pct']}%", f"{k['cancel_rate_pct']}%", k["best_carrier"]["name"], k["worst_airport"]["code"]]:
        assert str(v) in md

def test_tableau_extract_consistent():
    import csv
    rows = list(csv.DictReader(open(ROOT / "tableau/ontime_extract_2025.csv")))
    assert len(rows) > 1000 and len({r["origin"] for r in rows}) == 30
    k = json.loads((ROOT / "reports/kpis.json").read_text())
    assert all(int(r["on_time"]) <= int(r["operated"]) <= int(r["scheduled_flights"]) for r in rows)
    assert sum(int(r["scheduled_flights"]) for r in rows) < k["flights"]

@pytest.mark.skipif(not (ROOT / "data/warehouse.duckdb").exists(), reason="full data not downloaded")
def test_full_data_kpis():
    c = duckdb.connect(str(ROOT / "data/warehouse.duckdb"), read_only=True)
    k = json.loads((ROOT / "reports/kpis.json").read_text())
    assert c.execute("SELECT COUNT(*) FROM stg_flights").fetchone()[0] == k["flights"]
    assert c.execute("SELECT COUNT(*) FROM stg_flights WHERE flight_date IS NULL OR carrier_code IS NULL").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(DISTINCT strftime(flight_date,'%Y-%m')) FROM stg_flights").fetchone()[0] == 12
