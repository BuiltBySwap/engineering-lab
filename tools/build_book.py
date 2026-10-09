#!/usr/bin/env python3
"""Build the book pages from the daily data files.

Source of truth (edit these):
  data/days/<YYYY-MM-DD>.yaml                 one file per day: session, Mobile Exploration Q&A, English, Role lens
  data/mobile-exploration/bank.yaml           the question bank (static)

Generated (never edit, not committed):
  docs/days/*.md                              one page per day
  docs/mobile-exploration/*.md                overview + one page per category
  docs/english/index.md, vocabulary.md        word of the day, day-wise table, all words by week
  docs/role-lens/index.md, models.md          role ladder, day-wise table, thinking models
  docs/status.md, docs/status.json            totals + what is still open (the cheap file to read first)

Run it before `mkdocs build` (the GitHub Action does this). Set BOOK_TODAY=YYYY-MM-DD to test another date.
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DAYS = ROOT / "data" / "days"
BANK = ROOT / "data" / "mobile-exploration" / "bank.yaml"
DOCS = ROOT / "docs"
STATUSES = ["todo", "partial", "done", "skipped"]
ICON = {"done": "✅", "partial": "🟡", "todo": "⬜", "skipped": "⏭️"}

LADDER = [
    ("Mobile Dev", "Correct, fast, maintainable code", "How does it work? How do I test it? What breaks?"),
    ("Mobile Lead", "The whole mobile codebase and team standards", "What should our default be? How do we prevent this class of bug?"),
    ("Team Lead", "Delivery, people, cross-team alignment", "Who does what by when? What is the risk? Who needs to know?"),
    ("CTO", "Business outcome, cost, risk, hiring", "Does this move the business? Build or buy? What will it cost in a year?"),
]


def today() -> date:
    override = os.environ.get("BOOK_TODAY")
    if override:
        return date.fromisoformat(override)
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).date()


def cell(text, limit=0) -> str:
    out = str(text or "").replace("|", "\\|").replace("\n", " ").strip()
    return out if not limit or len(out) <= limit else out[: limit - 1].rstrip() + "…"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_days() -> list[dict]:
    days = []
    for path in sorted(DAYS.glob("*.yaml")):
        try:
            rec = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as err:
            sys.exit(f"ERROR {path.name}: invalid YAML: {err}")
        rec["date"] = str(rec.get("date"))
        if rec["date"] != path.stem:
            sys.exit(f"ERROR {path.name}: date '{rec['date']}' must match the file name")
        for key in ("session", "mq", "english", "lens"):
            if key not in rec:
                sys.exit(f"ERROR {path.name}: missing '{key}'")
        for q in rec["mq"] or []:
            if q.get("status") not in STATUSES:
                sys.exit(f"ERROR {path.name}: {q.get('id')} status must be one of {STATUSES}")
        for part in ("english", "lens"):
            if rec[part].get("status") not in STATUSES:
                sys.exit(f"ERROR {path.name}: {part}.status must be one of {STATUSES}")
        rec["mq"] = rec["mq"] or []
        days.append(rec)
    return days


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def bullets(items) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_nothing yet_"


def day_page(rec, prev_day, next_day, has_notebook) -> str:
    sid = rec["session"]
    session = f"[{sid} · {rec['session_title']}](../topics/{sid}.ipynb)" if has_notebook else f"{sid} · {rec['session_title']}"
    lines = [f"# {rec['date']} · {rec['day']} · {sid}", "",
             f"**Session:** {session} · track: {rec['track']} · {rec['hours']} h · week {rec['week']}", "",
             "## Mobile Exploration", ""]
    if not rec["mq"]:
        lines += ["No question today.", ""]
    for q in rec["mq"]:
        lines += [f"### {q['id']} · {q['category']} {ICON[q['status']]}", "",
                  f"**Question:** {q['question']}", "",
                  f"**My guess:** {q.get('guess') or '_not written yet_'}", "",
                  f"**Answer:** {q.get('answer') or '_after I verify it_'}", "",
                  f"[All {q['category']} questions](../mobile-exploration/{slug(q['category'])}.md)", ""]
    eng = rec["english"]
    lines += [f"## English {ICON[eng['status']]}", ""]
    if eng.get("words"):
        lines += ["| Word | Meaning |", "|---|---|"] + [f"| **{w['word']}** | {w['meaning']} |" for w in eng["words"]] + [""]
    else:
        lines += ["Practice day. Words of the week: " + ", ".join(eng.get("week_words") or []), ""]
    lines += [f"**Grammar of the week:** {eng['grammar']}", "", f"**Task:** {eng['task']}", "",
              "**My sentences:**", bullets(eng.get("sentences")), "", "**Feedback:**", bullets(eng.get("feedback")), ""]
    lens = rec["lens"]
    lines += [f"## Role lens · {lens['role']} {ICON[lens['status']]}", "", f"**Question:** {lens['question']}", "",
              f"**My answer:** {lens.get('my_answer') or '_not written yet_'}", "",
              f"**Model answer:** {lens.get('model_answer') or '_after I answer_'}", ""]
    nav = []
    if prev_day:
        nav.append(f"[← {prev_day}]({prev_day}.md)")
    if next_day:
        nav.append(f"[{next_day} →]({next_day}.md)")
    lines += ["---", " · ".join(nav), ""]
    return "\n".join(lines)


def main() -> None:
    now = today()
    days = load_days()
    if not days:
        sys.exit("No day files found in data/days/")
    bank = yaml.safe_load(BANK.read_text(encoding="utf-8"))
    notebooks = {p.stem for p in (DOCS / "topics").glob("*.ipynb")}

    # ----- per-day pages -----
    for i, rec in enumerate(days):
        write(DOCS / "days" / f"{rec['date']}.md",
              day_page(rec, days[i - 1]["date"] if i else None, days[i + 1]["date"] if i + 1 < len(days) else None, rec["session"] in notebooks))

    # ----- Mobile Exploration -----
    answers, sched_date = {}, {}
    for rec in days:
        for q in rec["mq"]:
            answers[q["id"]] = (q["status"], q.get("guess", ""), q.get("answer", ""))
            sched_date[q["id"]] = rec["date"]
    by_cat = defaultdict(list)
    for q in bank:
        by_cat[q["category"]].append(q)

    def qstatus(qid):
        return answers.get(qid, ("todo", "", ""))[0]

    totals = {s: sum(1 for q in bank if qstatus(q["id"]) == s) for s in STATUSES}
    scheduled = sum(1 for q in bank if q["id"] in sched_date)
    lines = ["# Mobile Exploration", "",
             "How does it really work? One question a day (two on weekends). **Guess first in 2 lines, then verify, then write the answer in 2 to 4 lines.**", "",
             f"**Questions:** {len(bank)} · scheduled in the plan: {scheduled} · ✅ {totals['done']} · 🟡 {totals['partial']} · ⬜ {totals['todo']}", "",
             "## By category", "", "| Category | Questions | ✅ | 🟡 | ⬜ |", "|---|---|---|---|---|"]
    for cat in sorted(by_cat):
        qs = by_cat[cat]
        c = {s: sum(1 for q in qs if qstatus(q["id"]) == s) for s in STATUSES}
        lines.append(f"| [{cat}]({slug(cat)}.md) | {len(qs)} | {c['done']} | {c['partial']} | {c['todo']} |")
    lines += ["", "## Day by day", "", "| Date | Session | Questions |", "|---|---|---|"]
    for rec in days:
        if rec["mq"]:
            marks = " ".join(f"{q['id']} {ICON[q['status']]}" for q in rec["mq"])
            bold = "**" if rec["date"] == now.isoformat() else ""
            lines.append(f"| {bold}[{rec['date']}](../days/{rec['date']}.md){bold} | {rec['session']} | {marks} |")
    write(DOCS / "mobile-exploration" / "index.md", "\n".join(lines) + "\n")
    for cat, qs in by_cat.items():
        lines = [f"# {cat}", "", f"[← Mobile Exploration](index.md) · {len(qs)} questions", "",
                 "| ID | Question | Scheduled | Status |", "|---|---|---|---|"]
        for q in qs:
            when = sched_date.get(q["id"])
            when_txt = f"[{when}](../days/{when}.md)" if when else "bonus"
            lines.append(f"| {q['id']} | {cell(q['question'])} | {when_txt} | {ICON[qstatus(q['id'])]} |")
        lines += ["", "## Answers", ""]
        answered = [q for q in qs if qstatus(q["id"]) != "todo"]
        if not answered:
            lines.append("_No answers yet._")
        for q in answered:
            st, guess, ans = answers[q["id"]]
            lines += [f"### {q['id']} {ICON[st]} {{#{q['id'].lower()}}}", "", f"**{q['question']}**", "",
                      f"**My guess:** {guess or '_not written yet_'}", "", f"**Answer:** {ans}", ""]
        write(DOCS / "mobile-exploration" / f"{slug(cat)}.md", "\n".join(lines) + "\n")

    # ----- English -----
    def eng_row(rec):
        e = rec["english"]
        what = ", ".join(w["word"] for w in e.get("words", [])) or "practice"
        bold = "**" if rec["date"] == now.isoformat() else ""
        return f"| {bold}[{rec['date']}](../days/{rec['date']}.md){bold} | {rec['day']} | {what} | {cell(e['grammar'])} | {ICON[e['status']]} |"

    todays = next((r for r in days if r["date"] == now.isoformat()), None)
    lines = ["# English: word of the day", "",
             "Two words a day (Mon to Fri), the week's grammar point, 3 sentences about the day's topic. Weekends: speaking or writing practice with the week's words.", ""]
    if todays and todays["english"].get("words"):
        lines += [f"## Today · {todays['date']}", "", "| Word | Meaning |", "|---|---|"]
        lines += [f"| **{w['word']}** | {w['meaning']} |" for w in todays["english"]["words"]]
        lines += ["", f"Grammar: **{todays['english']['grammar']}** · [today's page](../days/{todays['date']}.md)", ""]
    elif todays:
        lines += [f"## Today · {todays['date']}", "", f"Practice day: {todays['english']['task']}", ""]
    else:
        lines += ["_Today is outside the plan (26 Sep 2026 to 30 Apr 2027)._", ""]
    lines += ["See also: [all words by week](vocabulary.md) · [my error log](error-log.md)", "",
              "## Day by day", "", "| Date | Day | Words | Grammar | Status |", "|---|---|---|---|---|"]
    lines += [eng_row(r) for r in days]
    write(DOCS / "english" / "index.md", "\n".join(lines) + "\n")

    weeks = defaultdict(lambda: {"theme": "", "grammar": "", "start": "", "words": []})
    for rec in days:
        w = weeks[rec["week"]]
        w["theme"], w["grammar"] = rec["english"].get("theme", ""), rec["english"]["grammar"]
        w["start"] = w["start"] or rec["date"]
        for word in rec["english"].get("words", []):
            w["words"].append(word)
    lines = ["# Vocabulary by week", "", "Each week has a theme, a grammar point and 10 words (2 a day). Use 2 new words a week in real messages: using a word is what makes it stay.", ""]
    for wk in sorted(weeks):
        w = weeks[wk]
        lines += [f"## Week {wk} · {w['theme']}", "", f"Starts {w['start']} · grammar: **{w['grammar']}**", "", "| Word | Meaning |", "|---|---|"]
        lines += [f"| {x['word']} | {x['meaning']} |" for x in w["words"]]
        lines.append("")
    write(DOCS / "english" / "vocabulary.md", "\n".join(lines) + "\n")

    # ----- Role lens -----
    lines = ["# Role lens", "", "The same topic looks different from each seat. Each day has one question from one of these four seats; weekends add a thinking model.", "",
             "| Role | Optimises for | Always asks |", "|---|---|---|"]
    lines += [f"| **{r}** | {o} | {q} |" for r, o, q in LADDER]
    if todays:
        lens = todays["lens"]
        lines += ["", f"## Today · {lens['role']}", "", lens["question"], "", f"[today's page](../days/{todays['date']}.md)"]
    lines += ["", "See also: [thinking models by week](models.md)", "", "## Day by day", "", "| Date | Role | Question | Status |", "|---|---|---|---|"]
    for rec in days:
        l = rec["lens"]
        bold = "**" if rec["date"] == now.isoformat() else ""
        lines.append(f"| {bold}[{rec['date']}](../days/{rec['date']}.md){bold} | {cell(l['role'])} | {cell(l['question'], 110)} | {ICON[l['status']]} |")
    write(DOCS / "role-lens" / "index.md", "\n".join(lines) + "\n")
    lines = ["# Thinking models", "", "One model a week, practised on Saturday and applied in Sunday's review.", ""]
    for rec in days:
        if rec["day"] == "Sat":
            lines += [f"## Week {rec['week']} · {rec['lens'].get('model', '')}", "", cell(rec["lens"]["question"]), ""]
    write(DOCS / "role-lens" / "models.md", "\n".join(lines) + "\n")

    # ----- status -----
    due = [r for r in days if r["date"] <= now.isoformat()]

    def open_parts(rec):
        parts = []
        mqs = [q["id"] for q in rec["mq"] if q["status"] != "done"]
        if mqs:
            parts.append("mq:" + "+".join(mqs))
        if rec["english"]["status"] not in ("done", "skipped"):
            parts.append("english")
        if rec["lens"]["status"] not in ("done", "skipped"):
            parts.append("lens")
        return parts

    open_days = [{"date": r["date"], "session": r["session"], "open": open_parts(r)} for r in due if open_parts(r)]
    count = lambda getter: {s: sum(1 for r in due if getter(r) == s) for s in STATUSES}
    status = {
        "as_of": now.isoformat(),
        "plan": {"start": days[0]["date"], "end": days[-1]["date"], "days": len(days), "days_due": len(due)},
        "mobile_exploration": {"bank": len(bank), "scheduled": scheduled, **totals},
        "english_due_days": count(lambda r: r["english"]["status"]),
        "role_lens_due_days": count(lambda r: r["lens"]["status"]),
        "today": None if not todays else {
            "date": todays["date"], "session": todays["session"], "mq": [q["id"] for q in todays["mq"]],
            "words": [w["word"] for w in todays["english"].get("words", [])], "lens_role": todays["lens"]["role"]},
        "open_days": open_days,
    }
    progress = DOCS / "progress.json"
    if progress.exists():
        sessions = json.loads(progress.read_text(encoding="utf-8"))
        status["sessions"] = {**sessions["counts"], "open": [s["id"] for s in sessions["sessions"] if s["status"] != "done"]}
    write(DOCS / "status.json", json.dumps(status, ensure_ascii=False, separators=(",", ":")))

    lines = ["# Status", "", f"> Generated · as of **{now.isoformat()}**. Read this first.", "",
             "| Track | ✅ | 🟡 | ⬜ | ⏭️ |", "|---|---|---|---|---|"]
    if "sessions" in status:
        s = status["sessions"]
        lines.append(f"| Sessions | {s.get('done', 0)} | {s.get('partial', 0)} | {s.get('in-progress', 0) + s.get('not-started', 0)} | 0 |")
    m = status["mobile_exploration"]
    lines.append(f"| Mobile Exploration (all {m['bank']}) | {m['done']} | {m['partial']} | {m['todo']} | 0 |")
    e, l = status["english_due_days"], status["role_lens_due_days"]
    lines.append(f"| English (days due) | {e['done']} | {e['partial']} | {e['todo']} | {e['skipped']} |")
    lines.append(f"| Role lens (days due) | {l['done']} | {l['partial']} | {l['todo']} | {l['skipped']} |")
    lines += ["", "## Open days (due, not finished)", "", "| Date | Session | Open |", "|---|---|---|"]
    lines += [f"| [{d['date']}](days/{d['date']}.md) | {d['session']} | {', '.join(d['open'])} |" for d in open_days] or ["| – | – | nothing open |"]
    lines += ["", "Open sessions are listed on the [Progress](progress.md) page.", ""]
    write(DOCS / "status.md", "\n".join(lines))
    print(f"book built: {len(days)} days, {len(bank)} questions, {len(open_days)} open days (as of {now})")


if __name__ == "__main__":
    main()
