import pandas as pd
from functools import lru_cache
import pbp_parser.helper_funcs as hf
import pbp_parser.pbp_requests as pbp_r

class PlayByPlay:
    def __init__(self, game_id):
      self.game_id = game_id
      self.pbp_df = self._pbp_with_home_away_players(game_id)

    # TODO: Clean this code up
  
    def _get_starters_by_quarter(self, period: int, game_id: str) -> dict:

      home_away = hf.get_home_away(game_id)
      pbp = pbp_r.extract_data(pbp_r.play_by_play_url(game_id))
      subs = hf.get_substitutions(pbp)

      assert(period in pbp["PERIOD"].unique())

      first_event_of_period = subs.loc[subs.groupby(by=['PERIOD', 'PLAYER_ID'])['EVENTNUM'].idxmin()]
      players_subbed_in_at_each_period = first_event_of_period[first_event_of_period['SUB'] == 'IN'][['PLAYER_ID', 'PERIOD', 'SUB']]
      all_subs_at_each_period = subs.copy()[['PLAYER_ID', 'PERIOD', 'SUB']]

      low = hf.calculate_time_at_period(period) + 5
      high = hf.calculate_time_at_period(period + 1) - 5
      boxscore = pbp_r.advanced_boxscore_url(game_id, low, high)
      boxscore_players = pbp_r.extract_data(boxscore).copy()[['PLAYER_NAME', 'PLAYER_ID', 'TEAM_ABBREVIATION', 'TEAM_ID']]
      boxscore_players['PERIOD'] = period

      players_subbed_in_at_period = players_subbed_in_at_each_period[players_subbed_in_at_each_period['PERIOD'] == period]
      all_subs_at_period = all_subs_at_each_period[all_subs_at_each_period['PERIOD'] == period].copy()
      all_subs_at_period = all_subs_at_period.sort_index()
      all_subs_at_period["SUB_COUNT"] = all_subs_at_period['SUB'].apply(lambda x: 1 if x == 'IN' else -1)
      all_subs_at_period["SUB_COUNT"] = all_subs_at_period.groupby(by=['PLAYER_ID'])['SUB_COUNT'].cumsum()

      players_who_were_subbed_out = all_subs_at_period[all_subs_at_period["SUB_COUNT"] < 0]["PLAYER_ID"].to_list()
      players_subbed_in_at_period = players_subbed_in_at_period[~players_subbed_in_at_period["PLAYER_ID"].isin(players_who_were_subbed_out)]

      joined_players = pd.merge(boxscore_players, players_subbed_in_at_period, on=['PLAYER_ID', 'PERIOD'], how='left')
      joined_players = joined_players[pd.isnull(joined_players['SUB'])][['PLAYER_NAME', 'PLAYER_ID', 'TEAM_ID', 'PERIOD']]
      
      return_dict = {'Home': "", 'Away': ""}
      return_dict['Home'] = hf.list_to_str(joined_players[joined_players['TEAM_ID'] == home_away['Home']]["PLAYER_ID"].to_list())
      return_dict['Away'] = hf.list_to_str(joined_players[joined_players['TEAM_ID'] == home_away['Away']]["PLAYER_ID"].to_list())

      return return_dict
    
    # TODO: Clean this code up
    
    def _pbp_with_home_away_players(self, game_id: str):

      pbp_df = pbp_r.extract_data(pbp_r.play_by_play_url(game_id))
      home_away = hf.get_home_away(game_id)
      pbp_df["HOME_TEAM"] = home_away["Home"]
      pbp_df["AWAY_TEAM"] = home_away["Away"]
      pbp_df["HOME_PLAYERS"] = None
      pbp_df["AWAY_PLAYERS"] = None
      start_period_indices = pbp_df[pbp_df["EVENTMSGTYPE"] == 12].index
      
      for i in range(len(start_period_indices)):
        starters_in_quarter = self._get_starters_by_quarter(i + 1, game_id)
        pbp_df.at[start_period_indices[i], "HOME_PLAYERS"] =  starters_in_quarter["Home"]
        pbp_df.at[start_period_indices[i], "AWAY_PLAYERS"] =  starters_in_quarter["Away"]

      pbp_df["HOME_PLAYERS"] = pbp_df["HOME_PLAYERS"].ffill()
      pbp_df["AWAY_PLAYERS"] = pbp_df["AWAY_PLAYERS"].ffill()

      subs = pbp_df[pbp_df["EVENTMSGTYPE"] == 8][['PERIOD', 'EVENTNUM', 'PLAYER1_ID', 'PLAYER2_ID']].copy()
      subs.columns = ['PERIOD', 'EVENTNUM', 'OUT', 'IN']
      subs.sort_values(by=['PERIOD', 'EVENTNUM'], inplace=True)

      for i in range(len(subs)):
        
        quarter_of_sub = subs.at[subs.index[i], "PERIOD"]

        pbp_df_index_of_next_quarter = pbp_df[pbp_df["PERIOD"] == quarter_of_sub + 1]
        if len(pbp_df_index_of_next_quarter) == 0:
          pbp_df_index_of_next_quarter = len(pbp_df)
        else:
          pbp_df_index_of_next_quarter = pbp_df_index_of_next_quarter.index[0]

        home_players_list = hf.str_to_list(pbp_df.at[subs.index[i], "HOME_PLAYERS"])
        away_players_list = hf.str_to_list(pbp_df.at[subs.index[i], "AWAY_PLAYERS"])

        out_player_id = str(int(subs.at[subs.index[i], "OUT"]))
        in_player_id = str(int(subs.at[subs.index[i], "IN"]))
        slice_quarter = slice(subs.index[i] + 1, pbp_df_index_of_next_quarter)

        if out_player_id in home_players_list:
          home_players_list.remove(out_player_id)
          home_players_list.append(in_player_id)
          pbp_df.at[subs.index[i], "HOME_PLAYERS"] = hf.list_to_str(home_players_list)
          pbp_df.loc[slice_quarter, "HOME_PLAYERS"] = pbp_df["HOME_PLAYERS"].loc[subs.index[i]]

        else:

          if out_player_id not in away_players_list:
            period = subs.iloc[subs.loc[i]]["PERIOD"]
            eventnum = subs.iloc[subs.loc[i]]["EVENTNUM"]
            print(f"Error: More than five players in at once starting at {period}, {eventnum}")

          else: 
            away_players_list.remove(out_player_id)
            
          away_players_list.append(in_player_id)
          pbp_df.at[subs.index[i], "AWAY_PLAYERS"] = hf.list_to_str(away_players_list)
          pbp_df.loc[slice_quarter, "AWAY_PLAYERS"] = pbp_df["AWAY_PLAYERS"].loc[subs.index[i]]
          
      return pbp_df
    
