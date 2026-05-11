# brasileirao-brasileirao-schedule-strength

Schedule Strength analyzer for Brasileirão Série A teams using ESPN data.

## Overview

This project calculates a **Weighted Remaining Schedule Strength (SOS)** for all 20 teams in the Brasileirão Série A. Unlike traditional SOS metrics, this implementation accounts for the home/away factor — which has significantly more impact in Brazilian football than in other leagues.

The formula used:

```
SOS = Σ(opponent_performance × home_away_weight) / number_of_matches
```

Where:
- `opponent_performance` = opponent's points / (matches played × 3)
- `home_away_weight` = 1.2 if the opponent plays at home, 0.8 if away

Only the next **5 matches** of each team in the Brasileirão are considered, making the metric more relevant for short-term analysis.

## Data Sources

All data is scraped from [ESPN Brasil](https://www.espn.com.br):
- **Standings** — points, wins, draws, losses per team
- **Fixtures** — next 5 Brasileirão matches per team, with home/away identification

## Project Structure

```
brasileirao-brasileirao-schedule-strength/
│
├── scrappers/
│   ├── scrapping_times.py       # Scrapes next 5 fixtures for all 20 teams
│   └── scrapping_classificacao.py # Scrapes current standings table
│
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting Started

**Requirements:** Python 3.12 (Playwright is not yet compatible with 3.14)

```bash
# Clone the repository
git clone https://github.com/hiurysousa/brasileirao-sos.git
cd brasileirao-sos

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium
```

**Run the scrapers:**

```bash
# Scrape standings
python scrappers/scrapping_classificacao.py

# Scrape fixtures for all 20 teams
python scrappers/scrapping_times.py
```

Both scripts generate CSV files used as input for the SOS analysis in pandas.

## Output

| File | Description |
|---|---|
| `classificacao.csv` | Current standings with points, wins, draws, losses and performance rate |
| `calendario.csv` | Next 5 Brasileirão fixtures per team with home/away situation |

## Roadmap

- [x] ESPN standings scraper
- [x] ESPN fixtures scraper (all 20 teams)
- [ ] SOS calculation with pandas
- [ ] Home/away weighted SOS
- [ ] Dashboard or visualization layer

## Author

**Hiury Sousa** — Computer Science student at IFCE, focused on Data Engineering.

[GitHub](https://github.com/hiurysousa) · [LinkedIn](https://linkedin.com/in/hiurysousa)
