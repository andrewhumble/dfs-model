import pandas as pd
from util.util import get_projection

week = 6
year = 2023

df = pd.read_csv(f'cache/weekly_{year}_projections.csv')
df['position'] = df[['position_QB', 'position_RB', 'position_TE', 'position_WR']].idxmax(axis=1).str.replace('position_', '')

# Drop players with a prediction lower than 5
df = df[df['prediction'] > 10]

# For each position, get the three players with the greatest increase in prediction from the previous week
starts_df = pd.DataFrame()
for position in ['QB', 'RB', 'WR', 'TE']:
    position_df = df[df['position'] == position]
    position_df['prediction_diff'] = (position_df['prediction'] - position_df['rolling_ppr']) / position_df['rolling_ppr']
    # Drop where prediction_diff is inf
    position_df = position_df[position_df['prediction_diff'] != float('inf')]
    position_df = position_df.sort_values('prediction_diff', ascending=False).reset_index(drop=True)
    position_df['rank'] = position_df.index + 1
    position_df = position_df[['rank', 'player_display_name', 'position', 'recent_team', 'opponent', 'prediction', 'rolling_ppr', 'prediction_diff']]
    starts_df = starts_df.append(position_df.head(3))

# Write to csv
starts_df.to_csv(f'week{week}_{year}_starts.csv')