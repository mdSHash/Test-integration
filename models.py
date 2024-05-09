from sqlalchemy.orm import Mapped,mapped_column
from db import Base


class Player_Matches_Info(Base):
    __tablename__ = "player_matches_info"
    match_id: Mapped[str] = mapped_column(primary_key=True)
    tournament: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    start_time: Mapped[str] = mapped_column()
    home_team: Mapped[str] = mapped_column()
    away_team: Mapped[str] = mapped_column()
    home_score: Mapped[str] = mapped_column()
    away_score: Mapped[str] = mapped_column()
    player_id: Mapped[str] = mapped_column()

# self.cursor.execute('''CREATE TABLE IF NOT EXISTS Player_matches_info
#                 (match_id TEXT PRIMARY KEY, tournament TEXT, status TEXT, start_time TEXT,
#                 home_team TEXT, away_team TEXT, home_score TEXT, away_score TEXT, player_id TEXT)''')


class Players_Main_Info(Base):
    __tablename__ = "players_main_info"
    player_id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    country: Mapped[str] = mapped_column()
    ranking: Mapped[int] = mapped_column()

# self.cursor.execute('''CREATE TABLE IF NOT EXISTS Players_main_info
#                  (player_id TEXT, name TEXT, country TEXT, ranking INTEGER, PRIMARY KEY (player_id))''')

class Live_Tennis_data(Base):
    __tablename__ = "live_tennis_data"
    id: Mapped[str] = mapped_column(primary_key=True)
    tournament: Mapped[str] = mapped_column()
    round: Mapped[str] = mapped_column()
    home_team: Mapped[str] = mapped_column()
    away_team: Mapped[str] = mapped_column()
    match_progress: Mapped[str] = mapped_column()
    period: Mapped[str] = mapped_column()
    home_score: Mapped[str] = mapped_column()
    away_score: Mapped[str] = mapped_column()
    statistic_group: Mapped[str] = mapped_column()
    statistic_name: Mapped[str] = mapped_column()
    home_stat: Mapped[str] = mapped_column()
    away_stat: Mapped[str] = mapped_column()
    home_player_id: Mapped[str] = mapped_column()
    away_player_id: Mapped[str] = mapped_column()

# self.cursor.execute('''CREATE TABLE IF NOT EXISTS Live_Tennis_Data
#                  (tournament TEXT, round TEXT, home_team TEXT, away_team TEXT, match_progress TEXT,
#                  period TEXT, home_score TEXT, away_score TEXT, statistic_group TEXT, statistic_name TEXT,
#                  home_stat TEXT, away_stat TEXT, home_player_id TEXT, away_player_id TEXT)''')
