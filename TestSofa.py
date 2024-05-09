from fastapi import FastAPI, Query, Depends
from models import Base,Players_Main_Info,Player_Matches_Info,Live_Tennis_data
from db import get_db, engine
from schemas import LiveTennisData,PlayerMatchInfo,PlayerMainInfo
from sqlalchemy.orm import Session
from typing import List, Optional
import psycopg2
import requests
import time
import random
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
HTTP_OK = 200
HTTP_FORBIDDEN = 403
HTTP_RETRY_MIN_DELAY = 10
HTTP_RETRY_MAX_DELAY = 30

# Initialize FastAPI
app = FastAPI()

# creates tables
Base.metadata.create_all(bind=engine)






# Routes with pagination
@app.get("/live_tennis_data/", response_model=List[LiveTennisData])
def get_live_tennis_data(db:Session = Depends(get_db)):

    data = db.query(Live_Tennis_data).all()
    return data


@app.get("/player_matches_info/", response_model=List[PlayerMatchInfo])
def get_player_matches_info(db:Session = Depends(get_db)):
    data = db.query(Player_Matches_Info).all()
    return data


@app.get("/players_main_info/", response_model=List[PlayerMainInfo])
def get_players_main_info(db:Session = Depends(get_db)):

    data = db.query(Players_Main_Info).all()
    return data


class TennisStatsTracker:
    def __init__(self, db_config):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()

    def fetch_statistics(self, event_id):
        url = f'https://api.sofascore.com/api/v1/event/{event_id}/statistics'
        response = requests.get(url, headers=self.headers)
        if response.status_code == HTTP_OK:
            return response.json()
        elif response.status_code == HTTP_FORBIDDEN:
            logger.error(f"Failed to fetch statistics for event ID {event_id}. Forbidden: You may be rate-limited or unauthorized.")
            return None
        else:
            logger.error(f"Failed to fetch statistics for event ID {event_id}. Status code: {response.status_code}")
            return None

    def extract_statistics(self, statistics_data, group_name, statistic_name):
        for group in statistics_data.get('statistics', []):
            if group['period'] == 'ALL':
                for subgroup in group['groups']:
                    if subgroup['groupName'] == group_name:
                        for statistic in subgroup['statisticsItems']:
                            if statistic['name'] == statistic_name:
                                return statistic['home'], statistic['away']
        return 'N/A', 'N/A'

    def create_table_if_not_exists(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS live_tennis_data
                 (id TEXT, tournament TEXT, round TEXT, home_team TEXT, away_team TEXT, match_progress TEXT, 
                 period TEXT, home_score TEXT, away_score TEXT, statistic_group TEXT, statistic_name TEXT, 
                 home_stat TEXT, away_stat TEXT, home_player_id TEXT, away_player_id TEXT)''')
        self.conn.commit()

    def truncate_table(self):
        self.cursor.execute("TRUNCATE live_tennis_data")
        self.conn.commit()

    def create_player_table_if_not_exists(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS players_main_info
                 (player_id TEXT, name TEXT, country TEXT, ranking INTEGER, PRIMARY KEY (player_id))''')
        self.conn.commit()

    def insert_player_data(self, player_data):
        try:
            self.cursor.execute("INSERT INTO players_main_info VALUES (%s, %s, %s, %s) ON CONFLICT (player_id) DO NOTHING", player_data)
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Error inserting player data: {e}")

    def create_player_matches_table_if_not_exists(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS player_matches_info
                (match_id TEXT PRIMARY KEY, tournament TEXT, status TEXT, start_time TEXT, 
                home_team TEXT, away_team TEXT, home_score TEXT, away_score TEXT, player_id TEXT)''')
        self.conn.commit()

    def insert_match_data(self, match_data):
        try:
            self.cursor.execute('''INSERT INTO player_matches_info
                                (match_id, tournament, status, start_time, home_team, away_team, 
                                home_score, away_score, player_id) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (match_id) DO NOTHING''',
                                (match_data['id'], match_data['tournament'], match_data['status'], match_data['start_time'],
                                    match_data['home_team'], match_data['away_team'], match_data['home_score'],
                                    match_data['away_score'], match_data['player_id']))
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Error inserting match data: {e}")


    def fetch_player_data(self, player_id):
        url = f'https://api.sofascore.com/api/v1/team/{player_id}/events/last/0'
        response = requests.get(url, headers=self.headers)
        if response.status_code == HTTP_OK:
            return response.json()
        else:
            logger.error(f"Failed to fetch player data for player ID {player_id}. Status code: {response.status_code}")
            return None

    def retrieve_and_store_players_data(self, events):
        player_ids = set()  # Using a set to ensure unique player IDs
        for event in events:
            player_ids.add(event['homeTeam']['id'])
            player_ids.add(event['awayTeam']['id'])

        for player_id in player_ids:
            player_data = self.fetch_player_data(player_id)
            if player_data:
                self.store_player_data(player_data, player_id)

    def store_player_data(self, player_data, player_id):
        home_team = player_data['events'][0]['homeTeam']
        name = home_team.get('name', 'Unknown')
        country = home_team.get('country', {}).get('name', 'Unknown')
        ranking = int(home_team.get('ranking', 0))
        player_info = (
            str(player_id),
            name,
            country,
            ranking
        )
        self.insert_player_data(player_info)
        self.store_player_matches(player_data['events'], player_id)

    def store_player_matches(self, events, player_id):
        for event in events:
            tournament_name = event['tournament']['name'] if 'tournament' in event else 'Unknown'
            home_score = event['homeScore'].get('current', 'N/A')
            away_score = event['awayScore'].get('current', 'N/A')
            if event['status']['type'] == 'finished':
                home_score = event['homeScore'].get('display', 'N/A')
                away_score = event['awayScore'].get('display', 'N/A')
            match = {
                'id': event['id'],
                'tournament': tournament_name,
                'status': event['status']['description'],
                'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(event['startTimestamp'])),
                'home_team': event['homeTeam']['name'],
                'away_team': event['awayTeam']['name'],
                'home_score': home_score,
                'away_score': away_score,
                'player_id': player_id
            }
            self.insert_match_data(match)

    def insert_data(self, data):
        try:
            self.cursor.execute("INSERT INTO live_tennis_data VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", data)
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Error inserting data: {e}")

    def track_stats(self):
        while True:
            response = requests.get('https://api.sofascore.com/api/v1/sport/tennis/events/live', headers=self.headers)
            if response.status_code == HTTP_OK:
                live = response.json()
                self.truncate_table()
                self.retrieve_and_store_players_data(live['events'])
                for event in live['events']:
                    event_id = event['id']
                    data = (
                        event_id,
                        event['tournament']['name'], event['roundInfo']['name'], event['homeTeam']['name'],
                        event['awayTeam']['name'], event['status']['description'], 'ALL',
                        event['homeScore']['current'], event['awayScore']['current'], '', '', '', '',
                        event['homeTeam']['id'], event['awayTeam']['id']  # Include player IDs
                    )
                    statistics = self.fetch_statistics(event_id)
                    if statistics:
                        statistics_mapping = {
                            "Service": ["Aces", "Double faults", "First serve", "Second serve",
                                        "First serve points", "Second serve points", "Service games played", "Break points saved"],
                            "Points": ["Total", "Service points won", "Receiver points won", "Max points in a row"],
                            "Games": ["Total", "Service games won", "Max games in a row"],
                            "Return": ["First serve return points", "Second serve return points", "Return games played", "Break points converted"]
                        }
                        for group, stats in statistics_mapping.items():
                            for stat_name in stats:
                                home_stat, away_stat = self.extract_statistics(statistics, group, stat_name)
                                data = data[:8] + (group, stat_name, home_stat, away_stat) + data[12:]  # Preserve player IDs
                                self.insert_data(data)
                    else:
                        self.insert_data(data)
                random_delay = random.randint(HTTP_RETRY_MIN_DELAY, HTTP_RETRY_MAX_DELAY)
                logger.info(f"Waiting for {random_delay} seconds before fetching data again...")
                time.sleep(random_delay)
            else:
                logger.error(f"Failed to retrieve data. Status code: {response.status_code}")


if __name__ == "__main__":
    tracker = TennisStatsTracker({"dbname": "Tennis_Sofa", "user": "postgres", "password": "123", "host": "localhost", "port": "5432"})
    tracker.create_table_if_not_exists()
    tracker.create_player_table_if_not_exists()
    tracker.create_player_matches_table_if_not_exists()
    tracker.track_stats()
