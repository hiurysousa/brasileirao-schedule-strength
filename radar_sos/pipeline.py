"""Coleta da ESPN e cálculo reproduzível do Radar SOS."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://site.api.espn.com/apis"
PRIOR_GAMES = 5
NEXT_GAMES = 5


def source_urls(season: int) -> dict[str, str]:
    return {
        "standings": f"{BASE_URL}/v2/sports/soccer/bra.1/standings?season={season}",
        "schedule": f"{BASE_URL}/site/v2/sports/soccer/bra.1/scoreboard?dates={season}&limit=500",
    }


def fetch_season(season: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Obtém duas respostas JSON; nenhuma página HTML ou navegador é necessário."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"Accept": "application/json"})
    urls = source_urls(season)
    responses = []
    for url in (urls["standings"], urls["schedule"]):
        response = session.get(url, timeout=30)
        response.raise_for_status()
        responses.append(response.json())
    return responses[0], responses[1]


def _entries(node: dict[str, Any]) -> list[dict[str, Any]]:
    found = list(node.get("standings", {}).get("entries", []))
    for child in node.get("children", []):
        found.extend(_entries(child))
    return found


def parse_standings(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    teams = {}
    for entry in _entries(payload):
        team = entry["team"]
        team_id = str(team["id"])
        stats = {stat["name"]: stat.get("value") for stat in entry["stats"]}
        games = int(stats["gamesPlayed"])
        points = int(stats["points"])
        if team_id in teams or games < 0 or not 0 <= points <= 3 * games:
            raise ValueError(f"Classificação inconsistente para o ID {team_id}")
        logos = team.get("logos", [])
        teams[team_id] = {
            "id": team_id,
            "name": team.get("displayName") or team.get("name") or team_id,
            "abbreviation": team.get("abbreviation") or team_id,
            "logo": logos[0].get("href") if logos else None,
            "played": games,
            "points": points,
        }
    if len(teams) != 20:
        raise ValueError(f"Esperados 20 clubes da Série A; recebidos {len(teams)}")
    return teams


def _date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_events(payload: dict[str, Any], season: int, as_of: datetime) -> tuple[list[dict], list[dict]]:
    events = payload.get("events", [])
    if len(events) >= 500:
        raise ValueError("O calendário pode ter sido truncado pelo limite da ESPN")
    fixtures, results, seen = [], [], set()
    for event in events:
        if event.get("season", {}).get("year") != season or event["id"] in seen:
            continue
        seen.add(event["id"])
        competition = event.get("competitions", [{}])[0]
        opponents = competition.get("competitors", [])
        if len(opponents) != 2:
            continue
        sides = {item.get("homeAway"): item for item in opponents}
        if set(sides) != {"home", "away"}:
            continue
        event_date = _date(competition.get("date") or event["date"])
        item = {
            "id": str(event["id"]),
            "date": event_date.isoformat().replace("+00:00", "Z"),
            "home_id": str(sides["home"]["team"]["id"]),
            "away_id": str(sides["away"]["team"]["id"]),
        }
        status = competition.get("status", event.get("status", {})).get("type", {})
        if status.get("completed") and status.get("state") == "post":
            try:
                item["home_score"] = int(sides["home"]["score"])
                item["away_score"] = int(sides["away"]["score"])
            except (KeyError, TypeError, ValueError):
                raise ValueError(f"Placar final inválido: partida {event['id']}") from None
            results.append(item)
        elif status.get("state") == "pre" and event_date >= as_of:
            fixtures.append(item)
    fixtures.sort(key=lambda item: (item["date"], item["id"]))
    return fixtures, results


def build_snapshot(
    standings_payload: dict[str, Any],
    schedule_payload: dict[str, Any],
    season: int,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError("A data de referência precisa incluir fuso horário")
    teams = parse_standings(standings_payload)
    fixtures, results = parse_events(schedule_payload, season, as_of)
    for game in fixtures + results:
        if game["home_id"] not in teams or game["away_id"] not in teams:
            raise ValueError(f"Partida {game['id']} contém clube fora da classificação")
        if game["home_id"] == game["away_id"]:
            raise ValueError(f"Partida {game['id']} tem o mesmo mandante e visitante")

    venue = defaultdict(lambda: {"games": 0, "points": 0})
    for game in results:
        home, away = game["home_id"], game["away_id"]
        venue[(home, "home")]["games"] += 1
        venue[(away, "away")]["games"] += 1
        if game["home_score"] > game["away_score"]:
            venue[(home, "home")]["points"] += 3
        elif game["home_score"] < game["away_score"]:
            venue[(away, "away")]["points"] += 3
        else:
            venue[(home, "home")]["points"] += 1
            venue[(away, "away")]["points"] += 1

    total_games = sum(team["played"] for team in teams.values())
    league_rate = sum(team["points"] for team in teams.values()) / (3 * total_games) if total_games else 0.45
    for team in teams.values():
        overall = team["points"] / (3 * team["played"]) if team["played"] else league_rate
        team["overall_rate"] = round(overall, 4)
        team["venue"] = {}
        for side in ("home", "away"):
            record = venue[(team["id"], side)]
            if record["games"] > team["played"]:
                raise ValueError(f"Resultados excedem jogos da classificação: {team['name']}")
            # Cinco partidas virtuais na taxa geral reduzem a oscilação da amostra local.
            rate = (record["points"] / 3 + PRIOR_GAMES * overall) / (record["games"] + PRIOR_GAMES)
            team["venue"][side] = {
                "played": record["games"],
                "points": record["points"],
                "rate": round(rate, 4),
            }

    upcoming = defaultdict(list)
    for game in fixtures:
        for team_side, opponent_side in (("home", "away"), ("away", "home")):
            team_id = game[f"{team_side}_id"]
            opponent_id = game[f"{opponent_side}_id"]
            opponent = teams[opponent_id]
            upcoming[team_id].append({
                "id": game["id"],
                "date": game["date"],
                "opponent_id": opponent_id,
                "opponent": opponent["name"],
                "opponent_abbreviation": opponent["abbreviation"],
                "location": "casa" if team_side == "home" else "fora",
                "difficulty": opponent["venue"][opponent_side]["rate"],
            })

    rows = []
    for team in teams.values():
        games = upcoming[team["id"]][:NEXT_GAMES]
        rows.append({
            **team,
            "remaining": len(upcoming[team["id"]]),
            "next_games": games,
            "sos": round(sum(game["difficulty"] for game in games) / len(games), 4) if games else None,
        })
    rows.sort(key=lambda team: (team["sos"] is None, -(team["sos"] or 0), team["name"]))
    return {
        "season": season,
        "updated_at": as_of.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sources": source_urls(season),
        "method": {"next_games": NEXT_GAMES, "prior_games": PRIOR_GAMES},
        "completed_games": len(results),
        "scheduled_games": len(fixtures),
        "teams": rows,
    }
