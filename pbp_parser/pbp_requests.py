from functools import lru_cache
import requests
from pbp_parser import constants
import pandas as pd

"""
Get the base play by play URL
"""

def play_by_play_url(game_id: str) -> str:
    return (
      "https://stats.nba.com/stats/"
      +f"playbyplayv2/?gameId={game_id}&startPeriod=0&endPeriod=14"
    )

"""
Get the base box score URL
"""

def advanced_boxscore_url(game_id: str, start: int, end: int) -> str:
    return (
      "https://stats.nba.com/stats/"
      +f"boxscoreadvancedv2/?gameId={game_id}&startPeriod=0&endPeriod=14"
      +f"&startRange={start}&endRange={end}&rangeType=2"
    )

"""
Get the base box score URL
"""

def game_info_url(game_id: str) -> str:
    return (
      "https://stats.nba.com/stats/"
      +f"boxscoresummaryv2/?GameID={game_id}"
    )

"""
Gets panadas dataframe from url
"""

@lru_cache(maxsize=10)
def extract_data(url: str) -> pd.DataFrame:
    response = requests.get(url, headers=constants.HEADERS)
    data = response.json()

    return pd.DataFrame(
      data["resultSets"][0]["rowSet"], 
      columns=data["resultSets"][0]["headers"]
    )