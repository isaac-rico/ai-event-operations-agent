"""The full read-only tool surface. SQL and calculations stay in application code."""
from datetime import date
from .store import AS_OF, database

def retrieve(tool, event, window):
    if tool not in {"performance","deadlines","risks"}:
        raise ValueError("Unknown tool")
    with database() as db:
        rows = db.execute("""
          SELECT e.*, (SELECT COUNT(*) FROM registrations r WHERE r.event=e.id AND status='confirmed') confirmed,
                 d.due,d.label FROM events e JOIN deadlines d ON e.id=d.event
          WHERE (?='all' OR e.id=?) ORDER BY e.id
        """,(event,event)).fetchall()
    results = []
    for row in rows:
        gap = max(0,row["target"] - row["confirmed"])
        days = (date.fromisoformat(row["due"]) - AS_OF).days
        base = {"event":row["name"]}
        if tool == "performance":
            base.update(confirmed=row["confirmed"],target=row["target"],gap=gap,
                        attainment_pct=round(100*row["confirmed"]/row["target"],1))
        elif tool == "deadlines":
            if days > window:
                continue
            base.update(task=row["label"],due=row["due"],days=days)
        else:
            # Negative days are overdue. An open task inside two days takes precedence.
            priority = 1 if days < 0 else 2 if days <= 2 else 3 if gap else 4
            action = ("Confirm completion of "+row["label"] if priority <= 2 else
                      "Review outreach for the remaining seats" if gap else "Monitor registrations")
            base.update(priority=priority,gap=gap,task=row["label"],days=days,action=action)
        results.append(base)
    if tool == "deadlines":
        results.sort(key=lambda r:r["days"])
    if tool == "risks":
        results.sort(key=lambda r:(r["priority"],-r["gap"]))
    return results
