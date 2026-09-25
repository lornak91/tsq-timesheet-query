#!/usr/bin/env python3
"""tsq -- answer "how many hours per project in this date range?"

Reads plain-text timesheet logs (one entry per line) and prints a summary
of hours per project, optionally filtered to a project and/or date range.
"""

import argparse
import datetime
import json
import sys

LINE_FORMAT = "DATE START-END PROJECT [DESCRIPTION]"


class Entry:
    __slots__ = ("date", "start", "end", "project", "description", "source", "lineno")

    def __init__(self, date, start, end, project, description, source, lineno):
        self.date = date
        self.start = start
        self.end = end
        self.project = project
        self.description = description
        self.source = source
        self.lineno = lineno

    @property
    def hours(self):
        start_dt = datetime.datetime.combine(self.date, self.start)
        # end <= start means the entry crossed midnight (checked at parse time),
        # so the end time belongs to the following calendar day.
        end_date = self.date if self.end > self.start else self.date + datetime.timedelta(days=1)
        end_dt = datetime.datetime.combine(end_date, self.end)
        return (end_dt - start_dt).total_seconds() / 3600.0


def parse_line(raw, source, lineno):
    line = raw.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split(None, 3)
    if len(parts) < 3:
        raise ValueError(f"expected '{LINE_FORMAT}', got {len(parts)} field(s)")

    date_str, span_str, project = parts[0], parts[1], parts[2]
    description = parts[3] if len(parts) == 4 else ""

    try:
        date = datetime.date.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"bad date {date_str!r}, expected YYYY-MM-DD")

    if "-" not in span_str:
        raise ValueError(f"bad time range {span_str!r}, expected HH:MM-HH:MM")
    start_str, end_str = span_str.split("-", 1)
    try:
        start = datetime.time.fromisoformat(start_str)
        end = datetime.time.fromisoformat(end_str)
    except ValueError:
        raise ValueError(f"bad time range {span_str!r}, expected HH:MM-HH:MM")

    if end == start:
        raise ValueError(f"end time {end_str} is identical to start time {start_str}")

    return Entry(date, start, end, project, description, source, lineno)


def load_entries(paths):
    entries = []
    warnings = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                try:
                    entry = parse_line(raw, path, lineno)
                except ValueError as exc:
                    warnings.append(f"{path}:{lineno}: {exc}")
                    continue
                if entry is not None:
                    entries.append(entry)
    return entries, warnings


def filter_entries(entries, since, until, project):
    for e in entries:
        if since is not None and e.date < since:
            continue
        if until is not None and e.date > until:
            continue
        if project is not None and e.project != project:
            continue
        yield e


def summarize(entries):
    totals = {}
    counts = {}
    for e in entries:
        totals[e.project] = totals.get(e.project, 0.0) + e.hours
        counts[e.project] = counts.get(e.project, 0) + 1
    projects = [
        {"project": p, "hours": round(totals[p], 2), "entries": counts[p]}
        for p in sorted(totals)
    ]
    total_hours = round(sum(totals.values()), 2)
    total_entries = sum(counts.values())
    return projects, total_hours, total_entries


def format_human(projects, total_hours, total_entries, since, until, project_filter):
    lines = []
    span = f"{since or 'earliest'} to {until or 'latest'}"
    header = f"Timesheet summary {span}"
    if project_filter:
        header += f" (project={project_filter})"
    lines.append(header)

    if not projects:
        lines.append("no entries in range")
        return "\n".join(lines)

    name_w = max(7, max(len(p["project"]) for p in projects))
    lines.append(f"{'project'.ljust(name_w)}  {'hours':>7}  {'entries':>7}")
    for p in projects:
        lines.append(f"{p['project'].ljust(name_w)}  {p['hours']:7.2f}  {p['entries']:7d}")
    lines.append("-" * (name_w + 2 + 7 + 2 + 7))
    lines.append(f"{'total'.ljust(name_w)}  {total_hours:7.2f}  {total_entries:7d}")
    return "\n".join(lines)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tsq",
        description="Answer: how many hours per project in a given date range?",
    )
    parser.add_argument("files", nargs="+", help="timesheet log file(s) to read")
    parser.add_argument("--since", metavar="YYYY-MM-DD", help="only entries on or after this date")
    parser.add_argument("--until", metavar="YYYY-MM-DD", help="only entries on or before this date")
    parser.add_argument("--project", help="only entries for this project")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON instead of a table")
    return parser


def parse_date_arg(value, flag):
    if value is None:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise SystemExit(f"tsq: bad {flag} value {value!r}, expected YYYY-MM-DD")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    since = parse_date_arg(args.since, "--since")
    until = parse_date_arg(args.until, "--until")

    entries, warnings = load_entries(args.files)
    for w in warnings:
        print(f"tsq: skipping malformed entry: {w}", file=sys.stderr)

    matched = list(filter_entries(entries, since, until, args.project))
    projects, total_hours, total_entries = summarize(matched)

    if args.json:
        payload = {
            "since": args.since,
            "until": args.until,
            "project_filter": args.project,
            "projects": projects,
            "total_hours": total_hours,
            "total_entries": total_entries,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_human(projects, total_hours, total_entries, args.since, args.until, args.project))

    return 0


if __name__ == "__main__":
    sys.exit(main())
