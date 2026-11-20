"""Both planners use the same tools and evidence renderer."""
import os
import re
from .store import EVENTS, context, save
from .tools import retrieve

def mock_plan(question, focus):
    q = question.lower()
    preference = re.fullmatch(r"remember (?:a |my )?(\d{1,3})[- ]day deadline window[.!]?",q)
    if preference:
        days = int(preference[1])
        return ("preference","all",days) if 1 <= days <= 90 else ("clarify","all",None)
    if re.search(r"\b(delete|update|insert|drop|email|send|export|revenue|profit|private|secret|ignore|sql)\b",q):
        return "clarify","all",None
    matches = [e[0] for e in EVENTS if e[1].lower() in q or re.search(r"\b"+e[0]+r"\b",q)]
    if len(matches)>1:
        return "clarify","all",None
    event = matches[0] if matches else "all"
    if event=="all" and re.search(r"\b(it|its|that event|this event|there)\b",q):
        if not focus:
            return "clarify","all",None
        event = focus
    if event=="all" and re.search(r"\b(for|at|about)\s+(?!all\b|each\b|every\b|the portfolio\b)",q):
        return "clarify","all",None
    for tool, pattern in [("risks","risk|prioriti|recommend"),("deadlines","deadline|due|overdue"),
                          ("performance","registr|shortfall|performance|seats|target|signed up")]:
        if re.search(pattern,q):
            return tool,event,None
    return "clarify","all",None

def render(tool, rows):
    if not rows:
        return "No matching records in the snapshot."
    lines = []
    for r in rows:
        if tool == "performance":
            detail = f"{r['confirmed']}/{r['target']} confirmed ({r['attainment_pct']}%), {r['gap']} seats short."
        elif tool == "deadlines":
            detail = f"{r['task']} due {r['due']} ({r['days']} days from snapshot)."
        else:
            detail = f"P{r['priority']} · {r['action']}. Gap {r['gap']} seats. {r['task']} due in {r['days']} days."
        lines.append(f"{r['event']} — {detail}")
    return "\n".join(lines)

async def respond(question, session):
    history, window = context(session)
    focus = next((r["event"] for r in reversed(history) if r["event"]),None)
    tool,event,value = mock_plan(question.strip(),focus)
    mode = os.getenv("EVENTOPS_MODE","demo")
    rows = []
    if tool == "preference":
        answer = f"Saved your {value}-day deadline window."
    elif mode=="live":
        from .live import select
        tool,event,rows = await select(question,history,window)
        answer = render(tool,rows) if tool!="clarify" else "Please specify a supported metric and event."
    elif mode!="demo":
        raise ValueError("Invalid mode")
    elif tool=="clarify":
        answer = "Please specify a supported event and ask about registrations, deadlines, or risks."
    else:
        rows = retrieve(tool,event,window)
        answer = render(tool,rows)
    save(session,question,answer,event if event!="all" else None,value if tool=="preference" else None)
    return dict(answer=answer,tool=tool,event=event,evidence=rows,mode=mode)
