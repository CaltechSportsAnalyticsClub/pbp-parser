from functools import lru_cache
from pbp_parser import pbp_requests
import pandas as pd
import numpy as np

"""
Converts a list to a comma separated string
"""
def list_to_str(l):
    return ",".join(sorted([str(x) for x in l]))

"""
Converts a comma separated string to a list
"""

def str_to_list(s):
    return [str(x) for x in s.split(",")]

@lru_cache(maxsize=10)
def get_home_away(game_id: str) -> dict:
    home_away = pbp_requests.extract_data(pbp_requests.game_info_url(game_id))
    home_away_d = {'Home': 0, 'Away': 0}
    home_away_d['Home'] = home_away.iloc[0]['HOME_TEAM_ID']
    home_away_d['Away'] = home_away.iloc[0]['VISITOR_TEAM_ID']
    return home_away_d

def calculate_time_at_period(period: int):
    if period > 5:
        return (720 * 4 + (period - 5) * (5 * 60)) * 10
    else:
        return (720 * (period - 1)) * 10

def get_substitutions(pbp_df: pd.DataFrame) -> pd.DataFrame:
    subs_only = pbp_df[pbp_df["EVENTMSGTYPE"] == 8][['PERIOD', 'EVENTNUM', 'PLAYER1_ID', 'PLAYER2_ID']]
    subs_only.columns = ['PERIOD', 'EVENTNUM', 'OUT', 'IN']
    in_df = subs_only[['IN', 'PERIOD', 'EVENTNUM']].copy()
    in_df["SUB"] = 'IN'
    in_df.columns = ['PLAYER_ID', 'PERIOD', 'EVENTNUM', 'SUB']
    out_df = subs_only[['OUT', 'PERIOD', 'EVENTNUM']].copy()
    out_df["SUB"] = 'OUT'
    out_df.columns = ['PLAYER_ID', 'PERIOD', 'EVENTNUM', 'SUB']
    subs = pd.concat([in_df, out_df])
    return subs

def event_is_dreb(row):
  
  if not ((row["EVENTMSGTYPE"] == 4) and (row["EVENTMSGACTIONTYPE"] == 0)):
    return False
  
  rebounder_team = row["PLAYER1_TEAM_ID"]

  if np.isnan(rebounder_team):
    home_desc_is_nan = (row["HOMEDESCRIPTION"]) != (row["HOMEDESCRIPTION"])
    if home_desc_is_nan:
      rebounder_team = row["AWAY_TEAM"]
    else:
      rebounder_team = row["HOME_TEAM"]

  if row["PREVEVENTMSGTYPE"] != 2 and row["PREVEVENTMSGTYPE"] != 3: 
    return False
  
  shooter_team = row["PREV_PLAYER1_TEAM_ID"]
  return shooter_team != rebounder_team

def event_is_tov(row):
  return row["EVENTMSGTYPE"] == 5

def event_is_made_shot(row):
  is_made_fg = row["EVENTMSGTYPE"] == 1
  is_last_ft = row["EVENTMSGACTIONTYPE"] == 12 or row["EVENTMSGACTIONTYPE"] == 15
  made = row["SCORECHANGE"] != 0
  
  return (is_made_fg) or (is_last_ft and made)

def event_is_new_poss(row):
  return event_is_tov(row) or event_is_dreb(row) or event_is_made_shot(row)


