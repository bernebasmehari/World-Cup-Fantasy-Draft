import os, sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.team import Team

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

def main():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(bind=engine)

    try:
        rows = session.execute(text("SELECT DISTINCT team FROM players ORDER BY team")).fetchall()
        team_names = [r[0] for r in rows if r[0]]
        if not team_names:
            print("No teams found in players table — did seed_players.py run first?")
            sys.exit(1)

        inserted = 0
        for name in team_names:
            if not session.query(Team).filter_by(name=name).first():
                session.add(Team(name=name))
                inserted += 1
        session.commit()
        print(f"Inserted {inserted} new teams (found {len(team_names)} total).")
    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
