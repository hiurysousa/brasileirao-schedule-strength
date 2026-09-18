import unittest
from datetime import datetime, timezone

from schedule_strength.pipeline import build_snapshot, parse_standings


def standings():
    entries = []
    for number in range(1, 21):
        entries.append({
            "team": {"id": str(number), "displayName": f"Clube {number}", "abbreviation": f"C{number}"},
            "stats": [
                {"name": "gamesPlayed", "value": 2 if number <= 2 else 0},
                {"name": "points", "value": 3 if number <= 2 else 0},
            ],
        })
    return {"children": [{"standings": {"entries": entries}}]}


def event(number, date, home, away, state, scores=None):
    competitors = [
        {"homeAway": "home", "team": {"id": str(home)}},
        {"homeAway": "away", "team": {"id": str(away)}},
    ]
    if scores:
        competitors[0]["score"], competitors[1]["score"] = scores
    return {
        "id": str(number), "date": date, "season": {"year": 2026},
        "competitions": [{
            "date": date,
            "competitors": competitors,
            "status": {"type": {"state": state, "completed": state == "post"}},
        }],
    }


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.as_of = datetime(2026, 9, 18, tzinfo=timezone.utc)
        self.events = {"events": [
            event(1, "2026-09-01T20:00Z", 1, 2, "post", (2, 0)),
            event(2, "2026-09-02T20:00Z", 2, 1, "post", (1, 0)),
            event(3, "2026-09-20T20:00Z", 1, 2, "pre"),
            event(4, "2026-09-25T20:00Z", 2, 1, "pre"),
            event(5, "2026-09-01T20:00Z", 1, 2, "pre"),
        ]}

    def test_home_and_away_strength_are_smoothed_and_averaged(self):
        snapshot = build_snapshot(standings(), self.events, 2026, self.as_of)
        alpha = next(team for team in snapshot["teams"] if team["id"] == "1")
        self.assertEqual(snapshot["scheduled_games"], 2)
        self.assertEqual(alpha["remaining"], 2)
        self.assertEqual([game["location"] for game in alpha["next_games"]], ["casa", "fora"])
        self.assertAlmostEqual(alpha["next_games"][0]["difficulty"], 0.4167, places=4)
        self.assertAlmostEqual(alpha["next_games"][1]["difficulty"], 0.5833, places=4)
        self.assertEqual(alpha["sos"], 0.5)

    def test_unknown_opponent_stops_publication(self):
        self.events["events"][2]["competitions"][0]["competitors"][1]["team"]["id"] = "999"
        with self.assertRaisesRegex(ValueError, "fora da classificação"):
            build_snapshot(standings(), self.events, 2026, self.as_of)

    def test_incomplete_standings_stops_publication(self):
        bad = standings()
        bad["children"][0]["standings"]["entries"].pop()
        with self.assertRaisesRegex(ValueError, "20 clubes"):
            parse_standings(bad)


if __name__ == "__main__":
    unittest.main()
