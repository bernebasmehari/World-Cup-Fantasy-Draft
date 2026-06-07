"""
seed_players.py
---------------
Scrapes the 2026 FIFA World Cup squads from Wikipedia and inserts every player
into your PostgreSQL `players` table.

Run from your backend directory:
    python seed_players.py

Requires: requests, beautifulsoup4, sqlalchemy, psycopg2-binary, python-dotenv
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker

# ─── Config ────────────────────────────────────────────────────────────────────

# Load your .env file so DATABASE_URL is available
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

# Wikipedia URL for all 48 squads
WIKI_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"

# Map Wikipedia position codes to your app's position values
POSITION_MAP = {
    "GK": "GK",
    "DF": "DEF",
    "MF": "MID",
    "FW": "FWD",
}

# ─── SQLAlchemy Setup ───────────────────────────────────────────────────────────

Base = declarative_base()

class Player(Base):
    """Mirror of your Player model — keeps this script self-contained."""
    __tablename__ = "players"

    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String, index=True)
    team     = Column(String, index=True)
    position = Column(String, index=True)
    points   = Column(Integer, default=0)

# ─── Scraping ──────────────────────────────────────────────────────────────────

def scrape_players():
    """
    Fetch the Wikipedia page and parse every squad table.
    Returns a list of dicts: {name, team, position, points}
    """
    print(f"Fetching {WIKI_URL} ...")
    response = requests.get(WIKI_URL, headers={"User-Agent": "WorldDraftApp/1.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    players = []

    # Each country section has an <h2> or <h3> with the country name,
    # followed by a wikitable containing the squad.
    # Strategy: find all wikitables and walk backwards to find the team name.

    tables = soup.find_all("table", class_="wikitable")
    print(f"Found {len(tables)} squad tables")

    for table_index, table in enumerate(tables):
        # Walk backwards from this table to find the nearest heading with a team name
        team_name = None
        for sibling in table.find_all_previous():
            if sibling.name in ("h2", "h3"):
                # The heading text is the country name (strip edit links etc.)
                raw = sibling.get_text(separator=" ", strip=True)
                # Remove "[edit]" and similar suffixes Wikipedia adds
                team_name = raw.replace("[edit]", "").strip()
                break

        if not team_name:
            continue  # Skip tables we can't attribute to a country

        # Debug: print first data row of first table so we can inspect structure
        if table_index == 0:
            rows_debug = table.find_all("tr")
            print(f"\nDEBUG — Team: {team_name}")
            for row in rows_debug[:3]:
                tds = row.find_all("td")
                ths = row.find_all("th")
                print(f"  th cells: {[c.get_text(strip=True) for c in ths]}")
                print(f"  td cells: {[c.get_text(strip=True) for c in tds]}")

        # Each row in the table is a player
        rows = table.find_all("tr")
        for row in rows:
            # All data cells (td) in this row
            cells = row.find_all("td")
            if len(cells) < 3:
                continue  # Skip header rows (they use <th>)

            # Wikipedia squad table columns:
            # No. | Pos. | Player | DOB | Caps | Goals | Club
            # We only need Pos. (index 1) and Player (index 2)
            pos_cell    = cells[1].get_text(strip=True)  # e.g. "GK", "DF", "MF", "FW"
            # Player name is in a <th> cell, not <td>
            th_cells = row.find_all("th")
            if not th_cells:
                continue
            player_cell = th_cells[-1].get_text(strip=True)

            # Normalize position
            pos_clean = "".join(c for c in pos_cell if not c.isdigit()).strip()
            position = POSITION_MAP.get(pos_clean.upper())
            if not position:


                continue

            # Clean player name — remove "(captain)" and similar suffixes
            name = player_cell.replace("(captain)", "").strip()

            players.append({
                "name":     name,
                "team":     team_name,
                "position": position,
                "points":   0,
            })

    return players

# ─── Seeding ───────────────────────────────────────────────────────────────────

def seed(players):
    """Clear the players table and insert all scraped players."""
    engine  = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing players so we don't get duplicates on re-runs
        existing = session.query(Player).count()
        if existing > 0:
            print(f"Deleting {existing} existing players...")
            session.query(Player).delete()
            session.commit()

        # Bulk insert all players
        print(f"Inserting {len(players)} players...")
        session.bulk_insert_mappings(Player, players)
        session.commit()
        print("Done! Players seeded successfully.")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise

    finally:
        session.close()

# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    players = scrape_players()

    if not players:
        print("No players found — check the scraping logic.")
        sys.exit(1)

    # Preview first 5 players so you can sanity-check before inserting
    print("\nSample players:")
    for p in players[:5]:
        print(f"  {p['name']} | {p['team']} | {p['position']}")

    print(f"\nTotal players scraped: {len(players)}")
    confirm = input("Insert into database? (y/n): ")
    if confirm.lower() != "y":
        print("Aborted.")
        sys.exit(0)

    seed(players)