from datetime import date, datetime, timedelta
from models.database import get_db

PLAN_DAYS = {"monthly": 30, "quarterly": 90, "yearly": 365}
DEFAULT_PRICES = {"monthly": 1500.0, "quarterly": 4000.0, "yearly": 14000.0}
GENDERS = {"male", "female", "other", "prefer_not_to_say"}

def _today():
    return date.today()

def _parse_date(value, field):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field} must use YYYY-MM-DD format")

def _member_dict(row):
    return dict(row) if row else None

def _required(data, fields):
    missing = [f for f in fields if data.get(f) is None or str(data.get(f)).strip() == ""]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))

def _get_existing_member(conn, member_id):
    row = conn.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()
    if not row:
        raise LookupError(f"Member {member_id} not found")
    return row

def _refresh_status(conn, member_id=None):
    today = _today().isoformat()
    if member_id is None:
        conn.execute("UPDATE members SET membership_status=CASE WHEN membership_end < ? THEN 'expired' ELSE 'active' END", (today,))
    else:
        conn.execute("UPDATE members SET membership_status=CASE WHEN membership_end < ? THEN 'expired' ELSE 'active' END WHERE id=?", (today, member_id))

def create_member(data):
    required = ["name", "age", "gender", "weight", "fitness_goal", "plan"]
    _required(data, required)
    name = str(data["name"]).strip()
    if len(name) < 2 or len(name) > 100:
        raise ValueError("name must be between 2 and 100 characters")
    try:
        age = int(data["age"])
        weight = float(data["weight"])
    except (ValueError, TypeError):
        raise ValueError("age must be an integer and weight must be numeric")
    if not 12 <= age <= 100:
        raise ValueError("age must be between 12 and 100")
    if not 20 <= weight <= 350:
        raise ValueError("weight must be between 20 and 350 kg")
    gender = str(data["gender"]).lower()
    if gender not in GENDERS:
        raise ValueError("gender must be male, female, other, or prefer_not_to_say")
    plan = str(data["plan"]).lower()
    if plan not in PLAN_DAYS:
        raise ValueError("plan must be monthly, quarterly, or yearly")
    start = _parse_date(data.get("membership_start", data.get("join_date", _today().isoformat())), "membership_start")
    join_date = _parse_date(data.get("join_date", start.isoformat()), "join_date")
    end = start + timedelta(days=PLAN_DAYS[plan])
    amount = float(data.get("amount", DEFAULT_PRICES[plan]))
    if amount < 0:
        raise ValueError("amount cannot be negative")
    with get_db() as conn:
        cur = conn.execute("""INSERT INTO members
            (name,age,gender,weight,fitness_goal,join_date,plan,membership_start,membership_end,membership_status)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (name, age, gender, weight, str(data["fitness_goal"]).strip(), join_date.isoformat(), plan,
             start.isoformat(), end.isoformat(), "active" if end >= _today() else "expired"))
        member_id = cur.lastrowid
        conn.execute("""INSERT INTO payments(member_id,plan,amount,paid_on,period_start,period_end)
            VALUES(?,?,?,?,?,?)""", (member_id, plan, amount, _today().isoformat(), start.isoformat(), end.isoformat()))
        row = _get_existing_member(conn, member_id)
        return _member_dict(row)

def list_members(query=None, status=None):
    with get_db() as conn:
        _refresh_status(conn)
        sql = "SELECT * FROM members WHERE 1=1"
        params = []
        if query:
            sql += " AND (name LIKE ? OR fitness_goal LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        if status:
            normalized = status.lower()
            if normalized not in {"active", "expired"}:
                raise ValueError("status must be active or expired")
            sql += " AND membership_status=?"
            params.append(normalized)
        sql += " ORDER BY id DESC"
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

def get_member(member_id):
    with get_db() as conn:
        _refresh_status(conn, member_id)
        return dict(_get_existing_member(conn, member_id))

def update_member(member_id, data):
    allowed = {"name", "age", "gender", "weight", "fitness_goal"}
    updates = {k: data[k] for k in allowed if k in data}
    if not updates:
        raise ValueError("Provide at least one field to update: name, age, gender, weight, fitness_goal")
    with get_db() as conn:
        _get_existing_member(conn, member_id)
        if "name" in updates and (not str(updates["name"]).strip() or len(str(updates["name"]).strip()) > 100):
            raise ValueError("name must be between 1 and 100 characters")
        if "age" in updates:
            try: updates["age"] = int(updates["age"])
            except (ValueError, TypeError): raise ValueError("age must be an integer")
            if not 12 <= updates["age"] <= 100: raise ValueError("age must be between 12 and 100")
        if "weight" in updates:
            try: updates["weight"] = float(updates["weight"])
            except (ValueError, TypeError): raise ValueError("weight must be numeric")
            if not 20 <= updates["weight"] <= 350: raise ValueError("weight must be between 20 and 350 kg")
        if "gender" in updates:
            updates["gender"] = str(updates["gender"]).lower()
            if updates["gender"] not in GENDERS: raise ValueError("Invalid gender")
        if "name" in updates: updates["name"] = str(updates["name"]).strip()
        if "fitness_goal" in updates: updates["fitness_goal"] = str(updates["fitness_goal"]).strip()
        assignments = ", ".join(f"{key}=?" for key in updates)
        conn.execute(f"UPDATE members SET {assignments} WHERE id=?", (*updates.values(), member_id))
        return dict(_get_existing_member(conn, member_id))

def renew_membership(member_id, data):
    with get_db() as conn:
        member = _get_existing_member(conn, member_id)
        plan = str(data.get("plan", member["plan"])).lower()
        if plan not in PLAN_DAYS:
            raise ValueError("plan must be monthly, quarterly, or yearly")
        today = _today()
        old_end = _parse_date(member["membership_end"], "membership_end")
        start = max(today, old_end + timedelta(days=1))
        end = start + timedelta(days=PLAN_DAYS[plan])
        amount = float(data.get("amount", DEFAULT_PRICES[plan]))
        if amount < 0: raise ValueError("amount cannot be negative")
        conn.execute("""UPDATE members SET plan=?,membership_start=?,membership_end=?,membership_status='active' WHERE id=?""",
                     (plan, start.isoformat(), end.isoformat(), member_id))
        conn.execute("""INSERT INTO payments(member_id,plan,amount,paid_on,period_start,period_end)
                     VALUES(?,?,?,?,?,?)""", (member_id, plan, amount, today.isoformat(), start.isoformat(), end.isoformat()))
        return dict(_get_existing_member(conn, member_id))

def record_attendance(data):
    _required(data, ["member_id"])
    try: member_id = int(data["member_id"])
    except (ValueError, TypeError): raise ValueError("member_id must be an integer")
    attended = _parse_date(data.get("attended_at", _today().isoformat()), "attended_at")
    with get_db() as conn:
        member = _get_existing_member(conn, member_id)
        if member["membership_end"] < _today().isoformat():
            raise ValueError("Cannot record attendance: membership is expired")
        cur = conn.execute("INSERT INTO attendance(member_id,attended_at,notes) VALUES(?,?,?)",
                           (member_id, attended.isoformat(), str(data.get("notes", ""))))
        return dict(conn.execute("""SELECT a.*,m.name AS member_name FROM attendance a JOIN members m ON m.id=a.member_id WHERE a.id=?""",
                                 (cur.lastrowid,)).fetchone())

def create_workout(data):
    _required(data, ["member_id", "exercise_name", "sets", "repetitions", "duration_minutes"])
    try:
        member_id = int(data["member_id"]); sets = int(data["sets"])
        reps = int(data["repetitions"]); duration = int(data["duration_minutes"])
    except (ValueError, TypeError):
        raise ValueError("member_id, sets, repetitions, and duration_minutes must be integers")
    if min(sets, reps, duration) <= 0:
        raise ValueError("sets, repetitions, and duration_minutes must be greater than zero")
    with get_db() as conn:
        _get_existing_member(conn, member_id)
        cur = conn.execute("""INSERT INTO workouts(member_id,exercise_name,sets,repetitions,duration_minutes,trainer_notes,assigned_date,trainer_name)
            VALUES(?,?,?,?,?,?,?,?)""",
            (member_id, str(data["exercise_name"]).strip(), sets, reps, duration,
             str(data.get("trainer_notes", "")), _today().isoformat(), str(data.get("trainer_name", ""))))
        return dict(conn.execute("SELECT * FROM workouts WHERE id=?", (cur.lastrowid,)).fetchone())

def list_workouts(member_id=None):
    with get_db() as conn:
        if member_id:
            return [dict(r) for r in conn.execute("""SELECT w.*,m.name AS member_name FROM workouts w JOIN members m ON m.id=w.member_id WHERE member_id=? ORDER BY w.id DESC""", (member_id,)).fetchall()]
        return [dict(r) for r in conn.execute("""SELECT w.*,m.name AS member_name FROM workouts w JOIN members m ON m.id=w.member_id ORDER BY w.id DESC""").fetchall()]

def get_member_workouts(member_id):
    with get_db() as conn:
        _get_existing_member(conn, member_id)
        return [dict(r) for r in conn.execute("SELECT * FROM workouts WHERE member_id=? ORDER BY id DESC", (member_id,)).fetchall()]

def record_progress(workout_id, data):
    try:
        completed_sets = int(data.get("completed_sets", 0))
        completed_reps = int(data.get("completed_repetitions", 0))
        completed_minutes = int(data.get("completed_minutes", 0))
    except (ValueError, TypeError):
        raise ValueError("Progress values must be integers")
    if min(completed_sets, completed_reps, completed_minutes) < 0:
        raise ValueError("Progress values cannot be negative")
    with get_db() as conn:
        workout = conn.execute("SELECT * FROM workouts WHERE id=?", (workout_id,)).fetchone()
        if not workout: raise LookupError(f"Workout {workout_id} not found")
        complete = int(completed_sets >= workout["sets"] and completed_reps >= workout["repetitions"] and completed_minutes >= workout["duration_minutes"])
        cur = conn.execute("""INSERT INTO workout_progress(workout_id,completed_sets,completed_repetitions,completed_minutes,completed,notes,logged_at)
            VALUES(?,?,?,?,?,?,?)""", (workout_id, completed_sets, completed_reps, completed_minutes, complete,
                                      str(data.get("notes", "")), datetime.now().isoformat(timespec="seconds")))
        return dict(conn.execute("SELECT * FROM workout_progress WHERE id=?", (cur.lastrowid,)).fetchone())

def get_analytics():
    with get_db() as conn:
        _refresh_status(conn)
        today = _today()
        month_start = today.replace(day=1).isoformat()
        members = conn.execute("SELECT * FROM members").fetchall()
        active = sum(m["membership_status"] == "active" for m in members)
        expired = sum(m["membership_status"] == "expired" for m in members)
        monthly_new = conn.execute("SELECT COUNT(*) FROM members WHERE join_date >= ?", (month_start,)).fetchone()[0]
        registrations = [dict(r) for r in conn.execute("""SELECT substr(join_date,1,7) AS month,COUNT(*) AS registrations
            FROM members GROUP BY month ORDER BY month""").fetchall()]
        attendance = [dict(r) for r in conn.execute("""SELECT substr(attended_at,1,7) AS month,COUNT(*) AS visits
            FROM attendance GROUP BY month ORDER BY month""").fetchall()]
        popular = [dict(r) for r in conn.execute("""SELECT exercise_name,COUNT(*) AS assignments
            FROM workouts GROUP BY exercise_name ORDER BY assignments DESC LIMIT 10""").fetchall()]
        revenue = [dict(r) for r in conn.execute("""SELECT substr(paid_on,1,7) AS month,ROUND(SUM(amount),2) AS revenue
            FROM payments GROUP BY month ORDER BY month""").fetchall()]
        total_revenue = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments").fetchone()[0]
        attendance_today = conn.execute("SELECT COUNT(*) FROM attendance WHERE attended_at=?", (today.isoformat(),)).fetchone()[0]
        expiring_soon = conn.execute("SELECT COUNT(*) FROM members WHERE membership_end BETWEEN ? AND ?",
                                     (today.isoformat(), (today + timedelta(days=7)).isoformat())).fetchone()[0]
        progress = conn.execute("SELECT COUNT(*) FROM workout_progress WHERE completed=1").fetchone()[0]
        return {
            "summary": {"total_members": len(members), "active_members": active, "expired_memberships": expired,
                        "new_registrations_this_month": monthly_new, "attendance_today": attendance_today,
                        "memberships_expiring_within_7_days": expiring_soon, "total_recorded_revenue": round(total_revenue, 2),
                        "completed_workout_logs": progress},
            "member_growth_by_month": registrations,
            "attendance_by_month": attendance,
            "popular_workouts": popular,
            "revenue_by_month": revenue
        }
