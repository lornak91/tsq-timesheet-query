# tsq

I keep time entries in a plain text file, one line per stretch of work, and
every so often I need one number: how many hours did I spend on project X
between two dates. Opening a spreadsheet for that is annoying. `tsq` answers
just that question, from the log file, on the command line.

## Log format

One entry per line:

```
DATE START-END PROJECT [DESCRIPTION]
```

- `DATE` is `YYYY-MM-DD`.
- `START-END` is `HH:MM-HH:MM`, 24-hour clock, same day.
- `PROJECT` is a single token (no spaces) -- use a short slug.
- `DESCRIPTION` is free text, optional, everything to the end of the line.
- Blank lines and lines starting with `#` are ignored.

Example (see `sample_timesheet.txt`):

```
2026-09-14  09:00-11:30  acme       kickoff call and requirements notes
2026-09-14  13:00-17:00  acme       spec review with client
2026-09-15  09:00-12:00  internal   standup, planning, inbox
2026-09-16  10:00-15:30  bramble    migration script, first pass
```

## Usage

Total hours per project across a whole file:

```
$ python3 tsq.py sample_timesheet.txt
Timesheet summary earliest to latest
project   hours  entries
acme       6.50        3
bramble    8.00        2
internal   3.50        2
------------------------
total     18.00        7
```

Narrow to a date range and/or a single project:

```
$ python3 tsq.py sample_timesheet.txt --since 2026-09-16 --until 2026-09-17
Timesheet summary 2026-09-16 to 2026-09-17
project   hours  entries
bramble    8.00        2
------------------------
total      8.00        2

$ python3 tsq.py sample_timesheet.txt --project acme --json
{
  "since": null,
  "until": null,
  "project_filter": "acme",
  "projects": [
    {
      "project": "acme",
      "hours": 6.5,
      "entries": 2
    }
  ],
  "total_hours": 6.5,
  "total_entries": 2
}
```

Multiple log files can be passed at once and are merged before summarizing:

```
$ python3 tsq.py 2026-08.txt 2026-09.txt --since 2026-08-15
```

Malformed lines (bad date, bad time range, end before start) are reported to
stderr with file and line number, and skipped -- they do not stop the rest of
the file from being read.

## Requirements

Python 3.9+, standard library only. No install step beyond having Python.

## License

MIT, see `LICENSE`.
