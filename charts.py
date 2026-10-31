import pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).parent

def render(con, k):
    fig = plt.figure(figsize=(16, 10)); gs = fig.add_gridspec(3, 3, height_ratios=[0.5, 1.4, 1.4])
    cards = [("Flights scheduled", f"{k['flights']/1e6:.2f}M"), ("On-time arrival", f"{k['otp_pct']}%"),
             ("Cancelled", f"{k['cancel_rate_pct']}%")]
    for i, (t, v) in enumerate(cards):
        ax = fig.add_subplot(gs[0, i]); ax.axis("off")
        ax.text(0.5, 0.62, v, ha="center", fontsize=28, weight="bold", color="#1f4e79")
        ax.text(0.5, 0.15, t, ha="center", fontsize=13, color="#444")
    m = con.execute("SELECT month, SUM(on_time)/SUM(operated)*100, SUM(cancelled)/SUM(scheduled_flights)*100 FROM fct_carrier_month GROUP BY 1 ORDER BY 1").fetchall()
    ax = fig.add_subplot(gs[1, :2]); ax.plot([r[0] for r in m], [r[1] for r in m], marker="o", color="#1f4e79")
    ax.set_title("Monthly on-time arrival rate, 2025 (%)"); ax.grid(alpha=.3)
    ax2 = ax.twinx(); ax2.bar([r[0] for r in m], [r[2] for r in m], width=20, alpha=.25, color="#c0392b"); ax2.set_ylabel("cancel %")
    c = con.execute("SELECT d.carrier_name, SUM(on_time)/SUM(operated)*100 FROM fct_carrier_month JOIN dim_carrier d USING(carrier_code) GROUP BY 1 ORDER BY 2").fetchall()
    ax = fig.add_subplot(gs[1, 2]); ax.barh([r[0][:22] for r in c], [r[1] for r in c], color="#2e86c1")
    ax.set_title("OTP by carrier (%)"); ax.set_xlim(50, 100); ax.tick_params(labelsize=8)
    h = con.execute("SELECT sched_dep_hour, otp*100 FROM fct_hour WHERE scheduled_flights>10000 ORDER BY 1").fetchall()
    ax = fig.add_subplot(gs[2, 0]); ax.bar([r[0] for r in h], [r[1] for r in h], color="#5dade2")
    ax.set_title("OTP by scheduled departure hour"); ax.set_ylim(50, 100)
    s = k["delay_cause_share_pct"]
    ax = fig.add_subplot(gs[2, 1]); ax.pie(s.values(), labels=[x.replace("_", " ") for x in s], autopct="%1.0f%%", startangle=90)
    ax.set_title("Delay minutes by cause")
    a = con.execute("SELECT origin, otp*100 FROM fct_airport ORDER BY otp").fetchall()
    ax = fig.add_subplot(gs[2, 2]); ax.barh([r[0] for r in a], [r[1] for r in a], color="#48c9b0")
    ax.set_title("OTP, 30 busiest origin airports"); ax.set_xlim(55, 95); ax.tick_params(labelsize=7)
    fig.suptitle("US Airline On-Time Performance, 2025 (BTS Reporting Carrier data)", fontsize=17, weight="bold")
    fig.text(0.01, 0.005, "Source: US DOT Bureau of Transportation Statistics, Reporting Carrier On-Time Performance (1987-present), Jan-Dec 2025. Built by Amir Khan.", fontsize=9, color="#666")
    fig.tight_layout(rect=[0, 0.02, 1, 0.96]); fig.savefig(ROOT / "reports/dashboard.png", dpi=110); plt.close(fig)
