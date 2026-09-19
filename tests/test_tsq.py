import datetime
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import tsq


class ParseLineTests(unittest.TestCase):
    def test_full_entry(self):
        entry = tsq.parse_line(
            "2026-09-14  09:00-11:30  acme  kickoff call and requirements notes\n",
            "log.txt",
            1,
        )
        self.assertEqual(entry.date, datetime.date(2026, 9, 14))
        self.assertEqual(entry.start, datetime.time(9, 0))
        self.assertEqual(entry.end, datetime.time(11, 30))
        self.assertEqual(entry.project, "acme")
        self.assertEqual(entry.description, "kickoff call and requirements notes")
        self.assertEqual(entry.source, "log.txt")
        self.assertEqual(entry.lineno, 1)

    def test_entry_without_description(self):
        entry = tsq.parse_line("2026-09-14 09:00-11:30 acme", "log.txt", 1)
        self.assertEqual(entry.description, "")

    def test_blank_line_is_none(self):
        self.assertIsNone(tsq.parse_line("\n", "log.txt", 1))
        self.assertIsNone(tsq.parse_line("   \n", "log.txt", 1))

    def test_comment_line_is_none(self):
        self.assertIsNone(tsq.parse_line("# a note\n", "log.txt", 1))

    def test_too_few_fields(self):
        with self.assertRaisesRegex(ValueError, "field"):
            tsq.parse_line("2026-09-14 09:00-11:30\n", "log.txt", 1)

    def test_bad_date(self):
        with self.assertRaisesRegex(ValueError, "bad date"):
            tsq.parse_line("2026-13-40 09:00-11:30 acme\n", "log.txt", 1)

    def test_bad_time_range_missing_dash(self):
        with self.assertRaisesRegex(ValueError, "bad time range"):
            tsq.parse_line("2026-09-14 0900to1130 acme\n", "log.txt", 1)

    def test_bad_time_range_unparseable_time(self):
        with self.assertRaisesRegex(ValueError, "bad time range"):
            tsq.parse_line("2026-09-14 09:99-11:30 acme\n", "log.txt", 1)

    def test_end_before_start(self):
        with self.assertRaisesRegex(ValueError, "not after"):
            tsq.parse_line("2026-09-14 11:30-09:00 acme\n", "log.txt", 1)

    def test_end_equal_start(self):
        with self.assertRaisesRegex(ValueError, "not after"):
            tsq.parse_line("2026-09-14 09:00-09:00 acme\n", "log.txt", 1)


class SummarizeTests(unittest.TestCase):
    def _entry(self, date, start, end, project):
        return tsq.Entry(date, start, end, project, "", "log.txt", 1)

    def test_totals_and_counts_grouped_by_project(self):
        entries = [
            self._entry(datetime.date(2026, 9, 14), datetime.time(9, 0), datetime.time(11, 30), "acme"),
            self._entry(datetime.date(2026, 9, 14), datetime.time(13, 0), datetime.time(17, 0), "acme"),
            self._entry(datetime.date(2026, 9, 15), datetime.time(9, 0), datetime.time(12, 0), "internal"),
        ]
        projects, total_hours, total_entries = tsq.summarize(entries)
        self.assertEqual(
            projects,
            [
                {"project": "acme", "hours": 6.5, "entries": 2},
                {"project": "internal", "hours": 3.0, "entries": 1},
            ],
        )
        self.assertEqual(total_hours, 9.5)
        self.assertEqual(total_entries, 3)

    def test_projects_sorted_alphabetically(self):
        entries = [
            self._entry(datetime.date(2026, 9, 14), datetime.time(9, 0), datetime.time(10, 0), "zeta"),
            self._entry(datetime.date(2026, 9, 14), datetime.time(9, 0), datetime.time(10, 0), "alpha"),
        ]
        projects, _, _ = tsq.summarize(entries)
        self.assertEqual([p["project"] for p in projects], ["alpha", "zeta"])

    def test_hours_rounded_to_two_places(self):
        entries = [
            self._entry(datetime.date(2026, 9, 14), datetime.time(9, 0), datetime.time(9, 20), "acme"),
        ]
        projects, total_hours, _ = tsq.summarize(entries)
        self.assertEqual(projects[0]["hours"], 0.33)
        self.assertEqual(total_hours, 0.33)

    def test_empty_input(self):
        projects, total_hours, total_entries = tsq.summarize([])
        self.assertEqual(projects, [])
        self.assertEqual(total_hours, 0.0)
        self.assertEqual(total_entries, 0)


if __name__ == "__main__":
    unittest.main()
