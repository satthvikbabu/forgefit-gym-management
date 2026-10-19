from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from models.database import get_db

OUTPUT_DIR = Path("analytics/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_charts():
    with get_db() as conn:
        growth = pd.read_sql_query("""SELECT substr(join_date,1,7) month, COUNT(*) registrations
            FROM members GROUP BY month ORDER BY month""", conn)
        attendance = pd.read_sql_query("""SELECT substr(attended_at,1,7) month, COUNT(*) visits
            FROM attendance GROUP BY month ORDER BY month""", conn)
        workouts = pd.read_sql_query("""SELECT exercise_name, COUNT(*) assignments
            FROM workouts GROUP BY exercise_name ORDER BY assignments DESC LIMIT 10""", conn)
        revenue = pd.read_sql_query("""SELECT substr(paid_on,1,7) month, SUM(amount) revenue
            FROM payments GROUP BY month ORDER BY month""", conn)

    charts = [
        ("member_growth.png", growth, "month", "registrations", "Monthly Member Registrations", "Registrations"),
        ("attendance_trends.png", attendance, "month", "visits", "Monthly Attendance", "Visits"),
        ("workout_distribution.png", workouts, "exercise_name", "assignments", "Workout Program Distribution", "Assignments"),
        ("monthly_revenue.png", revenue, "month", "revenue", "Monthly Membership Revenue", "Revenue")
    ]
    generated = []
    for filename, df, x, y, title, ylabel in charts:
        fig, ax = plt.subplots(figsize=(9, 5))
        if df.empty:
            ax.text(0.5, 0.5, "No data available yet", ha="center", va="center", transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            if x == "exercise_name":
                ax.bar(df[x].astype(str), df[y])
                ax.tick_params(axis="x", rotation=35)
            else:
                ax.plot(df[x].astype(str), df[y], marker="o")
                ax.tick_params(axis="x", rotation=35)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(x.replace("_", " ").title())
        fig.tight_layout()
        path = OUTPUT_DIR / filename
        fig.savefig(path, dpi=150)
        plt.close(fig)
        generated.append(str(path).replace("\\", "/"))
    return generated
