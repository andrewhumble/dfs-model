import pandas as pd

def get_projection(player, week, year):
    df = pd.read_csv(f'cache/weekly_{year}_projections.csv')
    return df[(df['player_name'] == player) & (df['week'] == week)]['prediction'].values[0]
