"""Atualiza o JSON consumido pelo site: python -m schedule_strength."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .pipeline import build_snapshot, fetch_season


def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza os dados do Brasileirão pela ESPN")
    parser.add_argument("--season", type=int, default=datetime.now(timezone.utc).year)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data/processed/snapshot.json")
    args = parser.parse_args()
    standings, schedule = fetch_season(args.season)
    snapshot = build_snapshot(standings, schedule, args.season)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Atualizado: {args.output} | {len(snapshot['teams'])} times | {snapshot['scheduled_games']} jogos futuros")


if __name__ == "__main__":
    main()
