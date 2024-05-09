from pydantic import BaseModel


# Pydantic models
class LiveTennisData(BaseModel):
    __tablename__ = 'Live_Tennis_Data'
    id: str  # Specify the type annotation for id
    tournament: str
    round: str
    home_team: str
    away_team: str
    match_progress: str
    period: str
    home_score: str
    away_score: str
    statistic_group: str
    statistic_name: str
    home_stat: str
    away_stat: str
    home_player_id: str
    away_player_id: str



class PlayerMatchInfo(BaseModel):
    __tablename__ = 'Player_matches_info'
    match_id: str  # Specify the type annotation for match_id
    tournament: str
    status: str
    start_time: str
    home_team: str
    away_team: str
    home_score: str
    away_score: str
    player_id: str


class PlayerMainInfo(BaseModel):
    __tablename__ = 'Players_main_info'
    player_id: str  # Specify the type annotation for player_id
    name: str
    country: str
    ranking: int