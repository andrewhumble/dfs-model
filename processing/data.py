import nfl_data_py as nfl
import pandas as pd
import numpy as np
import random as rand
import re

cols_to_roll = None
matchups_df = None
year = None
week = None

def fix_changed_abbr(df):
    changed_abbr_dict = {
        'OAK': 'LV',
    }

    # For any team that changed their abbreviation, change the abbreviation in the matchups df
    for key, value in changed_abbr_dict.items():
        df.loc[df['away_team'] == key, 'away_team'] = value
        df.loc[df['home_team'] == key, 'home_team'] = value

    return df

def handle_rolling_averages(df):
    # define rolling window size
    rolling_window_size = 3

    # get a list of all columns that are not identifiers (player_id, player_name, player_display_name, position)
    global cols_to_roll

    # TODO: Address duplicate opponent col at some point
    cols_to_roll = [col for col in df.columns if col not in ['player_id', 'player_name', 'player_display_name', 'position', 'position_group', 'headshot_url', 'recent_team', 'season', 'season_type', 'season_type_prev_season', 'week', 'report_status', 'wopr_prev_season', 'wopr', 'fantasy_points', 'fantasy_points_ppr', 'opponent', 'opponent_team'] and 'prev_season' not in col]

    # Add a new row where week = 6 for each player
    for player in df['player_id'].unique():
        # Get the most recent week for each player
        most_recent_week = df[df['player_id'] == player]['week'].max()

        # Get the most recent row for each player
        most_recent_row = df[(df['player_id'] == player) & (df['week'] == most_recent_week)]

        # Create a new row for each player with week = 6
        new_row = most_recent_row.copy()
        new_row['week'] = week
        new_row [[cols_to_roll, 'fantasy_points', 'fantasy_points_ppr']] = None
        df = df.append(new_row)

    # Sort by player_id and week
    df = df.sort_values(by=['player_id', 'week'])
    df = df.reset_index(drop=True)

    # Add rolling ppr points column to factor recent performance
    df['rolling_ppr'] = df.groupby('player_id')['fantasy_points_ppr'].rolling(window=rolling_window_size, min_periods=1).mean().reset_index(drop=True)
    df['rolling_ppr'] = df['rolling_ppr'].shift(1)

    # apply rolling average to each stat column
    for col in cols_to_roll:
        df[col] = df.groupby('player_id')[col].rolling(window=rolling_window_size, min_periods=1).mean().reset_index(drop=True)

    # Shift rows to be predictive of the current week based on past data
    df[cols_to_roll] = df[cols_to_roll].shift(1)

    # Set the first week of each player to be the average of the previous season
    ## Group by player_id and get the first week for each player
    first_week_df = df.groupby('player_id')[['player_name', 'position', 'week', 'games_prev_season'] + cols_to_roll].min().reset_index()
    for player in first_week_df.to_dict('records'):
        if player['position'] == 'QB':
            # Set passing_yards = passing_yards_prev_season / 10
            for col in cols_to_roll:
                try:
                    df.loc[(df['player_id'] == player['player_id']) & (df['week'] == player['week']), col] = df.loc[df['player_id'] == player['player_id'], col+'_prev_season'] / player['games_prev_season']
                except:
                    pass

    return df

def handle_previous_season_stats(df):
    # Join columns from previous season with column prefix
    prev_season_df = nfl.import_seasonal_data([year-1])
    # prev_season_df = pd.read_csv(f'cache/seasonal_{year-1}.csv')
    prev_season_df = prev_season_df.add_suffix('_prev_season')
    prev_season_df = prev_season_df.rename(columns={'player_id_prev_season': 'player_id', 'fantasy_points_ppr_prev_season': 'last_year_ppr_points'})

    df = df.merge(prev_season_df, on='player_id', how='left')

    return df

def handle_normalization(df):
    # Normalize cols_to_roll ranging from  0 to 1
    for col in cols_to_roll:
        df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
    return df

def handle_def_rankings(df):
    def_rank_df = pd.read_csv(f'def_rank_cache/def_rankings_{year}.csv')

    for row in df.to_dict('records'):
        try:
            row['def_points_against'] = def_rank_df[(def_rank_df['Abbr'] == row['opponent']) & (def_rank_df['week'] == row['week']) & (def_rank_df['position'] == row['position'])]['rolling_avg'].values[0]
        except:
            # If no def ranking exists, set to most recent def ranking
            row['def_points_against'] = def_rank_df[(def_rank_df['Abbr'] == row['opponent']) & (def_rank_df['position'] == row['position'])]['rolling_avg'].values[-1]

        # Update df row with def_points_against
        df.loc[(df['player_id'] == row['player_id']) & (df['week'] == row['week']), 'def_points_against'] = row['def_points_against']

    return df

def get_opponent(team, week):
    matchup_loc_df = matchups_df[(matchups_df['week'] == week) & ((matchups_df['away_team'] == team) | (matchups_df['home_team'] == team))]
    if len(matchup_loc_df) == 0:
        return None
    else:
        return matchup_loc_df['away_team'].values[0] if matchup_loc_df['home_team'].values[0] == team else matchup_loc_df['home_team'].values[0]

def handle_betting(df):
    # Get total lines from matchups_df for each row given the week and team
    # df['total'] = df.apply(lambda x: matchups_df[(matchups_df['week'] == x['week']) & ((matchups_df['away_team'] == x['recent_team']) | (matchups_df['home_team'] == x['recent_team']))]['total_line'].values[0], axis=1)

    # Create dictionary mapping (week, team) tuples to total_line values
    total_dict = {(week, team): total_line
                for week, away_team, home_team, total_line in matchups_df[['week', 'away_team', 'home_team', 'total_line']].values
                for team in [away_team, home_team]}

    # Get list of unique teams for the given week from total_dict
    teams = list(set([team for wk, team in total_dict.keys() if wk == week]))

    # Drop from df if team is not in teams
    df = df[df['recent_team'].isin(teams)]

    # Use dictionary to lookup total_line values during apply()
    df['total'] = df.apply(lambda x: total_dict[(x['week'], x['recent_team'])], axis=1)

    # Get money lines from matchups_df for each row given the week and team.
    # If recent_team = away_team, use away_moneyline. Else, use home_moneyline
    # df['moneyline'] = df.apply(lambda x: matchups_df[(matchups_df['week'] == x['week']) & ((matchups_df['away_team'] == x['recent_team']) | (matchups_df['home_team'] == x['recent_team']))]['away_moneyline'].values[0] if x['recent_team'] == matchups_df[(matchups_df['week'] == x['week']) & ((matchups_df['away_team'] == x['recent_team']) | (matchups_df['home_team'] == x['recent_team']))]['away_team'].values[0] else matchups_df[(matchups_df['week'] == x['week']) & ((matchups_df['away_team'] == x['recent_team']) | (matchups_df['home_team'] == x['recent_team']))]['home_moneyline'].values[0], axis=1)
    
    # Create dictionary mapping (week, team) tuples to away_moneyline or home_moneyline values
    moneyline_dict = {(week, team): (away_moneyline, home_moneyline)
                    for week, away_team, home_team, away_moneyline, home_moneyline in matchups_df[['week', 'away_team', 'home_team', 'away_moneyline', 'home_moneyline']].values
                    for team in [away_team, home_team]}

    # Use dictionary to lookup moneyline values during apply()
    df['moneyline'] = df.apply(lambda x: moneyline_dict[(x['week'], x['recent_team'])][0] if x['recent_team'] == matchups_df[(matchups_df['week'] == x['week']) & ((matchups_df['away_team'] == x['recent_team']) | (matchups_df['home_team'] == x['recent_team']))]['away_team'].values[0] else moneyline_dict[(x['week'], x['recent_team'])][1], axis=1)

    return df

def handle_team_injuries(df):
    injuries_df = nfl.import_injuries([year])

    # Drop rows with report_status = None
    injuries_df = injuries_df[injuries_df['report_status'].notna()]

    # Create df with number of players with each injury status for each team in each week
    injury_status_report = injuries_df.groupby(['team', 'week', 'report_status']).size().unstack(fill_value=0).reset_index()

    # Add injury counts to df matching on team and week
    df = df.merge(injury_status_report, how='left', left_on=['recent_team', 'week'], right_on=['team', 'week'])

    # Rename columns
    df = df.rename(columns={'Questionable': 'team_questionable', 'Doubtful': 'team_doubtful', 'Out': 'team_out'})

    return df

def handle_injuries(df):
    injuries_df = nfl.import_injuries([year])

    # Drop rows with report_status = None
    injuries_df = injuries_df[injuries_df['report_status'].notna()]

    # If player is in injuries_df, mark player as injured for that week
    df['injured'] = df.apply(lambda x: 1 if x['player_display_name'] in injuries_df[injuries_df['week'] == x['week']]['full_name'].values else 0, axis=1)

    return df

def fix_depth_positions(df):
    # For each given week, assign depth_position from 1 to N by current depth_position values
    # This will account for injured players, allowing backups to move up in depth_position

    # Loop through each week and assign depth_position for each player for a given team and given position
    for week in df['week'].unique():
        for team in df['recent_team'].unique():
            for position in df['position'].unique():
                # Get df for given week, team, and position
                temp_df = df[(df['week'] == week) & (df['recent_team'] == team) & (df['position'] == position)]

                # Sort by depth_position
                temp_df = temp_df.sort_values(by='depth_position')

                # Assign depth_position from 1 to N
                temp_df['depth_position'] = range(1, len(temp_df) + 1)

                # Update df
                df.update(temp_df)

    return df

def add_fp_proj(df):
    # Read csv containing projections
    fp_proj_df = pd.read_csv(f'fp_proj_cache/fp_proj_{year}.csv')

    # Add fp_proj col to df matching on player_display_name and week
    # For loop through df
    for i, row in df.iterrows():

        # Get fp_proj for player_display_name and week
        try:
            fp_proj = fp_proj_df[(fp_proj_df['player_display_name'] == row['player_display_name']) & (fp_proj_df['week'] == row['week'])]['fp_proj'].values[0]
        except:
            fp_proj = 0
        # Add fp_proj to df
        df.at[i, 'fp_proj'] = fp_proj

    return df

def handle_dummies(df):
    # Create dummies for position, recent_team, opponent
    df = pd.get_dummies(df, columns=['position'])
    return df

# NOTICE: This will need to be updated for upcoming NFL season. Current method only keeps players that actually played.
# Will need a way to determine if a player is starting or not for a given week.
def handle_depth_positions(df):
    roster = nfl.import_depth_charts([year])
    # For each player, set their depth position to 'depth_position'
    for i, row in df.iterrows():
        try:
            df.at[i, 'depth_position'] = int(roster[(roster['full_name'] == row['player_display_name']) & (roster['week'] == row['week'])]['depth_team'].values[0])
        except:
            continue

    return df

def create_data(yr, wk):    
    global year
    year = yr
    global week
    week = wk

    mtch_df = nfl.import_schedules([year])[['away_team', 'home_team', 'week', 'total_line', 'away_moneyline', 'home_moneyline']]

    global matchups_df
    matchups_df = mtch_df

    df = pd.DataFrame(nfl.import_weekly_data([year]))

    df = nfl.clean_nfl_data(df)
    df = df[df['week'] != week]

    matchups_df = fix_changed_abbr(matchups_df) 

    # Drop cols that are not positions QB, RB, WR, TE
    df = df[df['position'].isin(['QB', 'RB', 'WR', 'TE'])]

    # Add method of retrieving opponent for given week
    df['opponent'] = df.apply(lambda x: get_opponent(x['recent_team'], x['week']), axis=1)

    df = handle_previous_season_stats(df)
    df = handle_rolling_averages(df)

    # Drop cols where week is not week
    df = df[df['week'] == week]

    # Drop cols containing prev_season data
    df = df.drop([col for col in df.columns if 'prev_season' in col], axis=1)

    df = handle_depth_positions(df)
    df = handle_def_rankings(df)
    df = handle_betting(df)
    df = handle_team_injuries(df)
    df = handle_injuries(df)
    df = add_fp_proj(df)
    df = fix_depth_positions(df)
    df = handle_dummies(df)

    df = df.fillna(0)

    df['fp_proj'] = pd.to_numeric(df['fp_proj'], errors='coerce')
    df = df[df['injured'] == 0]

    return df


# for year in range(2019, 2023):
#     matchups_df = nfl.import_schedules([year])[['away_team', 'home_team', 'week', 'total_line', 'away_moneyline', 'home_moneyline']]

#     df = pd.DataFrame(nfl.import_weekly_data([year]))
#     # df = pd.read_csv(f'cache/weekly_{year}.csv')
#     df = nfl.clean_nfl_data(df)

#     matchups_df = fix_changed_abbr(matchups_df) 

#     # Drop cols that are not positions QB, RB, WR, TE
#     df = df[df['position'].isin(['QB', 'RB', 'WR', 'TE'])]

#     # Add method of retrieving opponent for given week
#     df['opponent'] = df.apply(lambda x: get_opponent(x['recent_team'], x['week']), axis=1)

#     df = handle_previous_season_stats(df)
#     df = handle_rolling_averages(df)

#     # Drop cols containing prev_season data
#     df = df.drop([col for col in df.columns if 'prev_season' in col], axis=1)

#     df = handle_depth_positions(df)
#     df = handle_def_rankings(df)
#     df = handle_betting(df)
#     df = handle_team_injuries(df)
#     df = handle_injuries(df)
#     df = add_fp_proj(df)
#     df = fix_depth_positions(df)
#     df = handle_dummies(df)

#     df = df.fillna(0)

#     # Save normalized data
#     with open(f'data/{year}.csv', 'w') as f:
#         f.write(df.to_csv(index=False))

#     print(f"Data for {year} saved to data/{year}.csv")