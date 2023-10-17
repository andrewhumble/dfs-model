import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Scrapes points allowed to each position for each week in a given season for each position.
# Points allowed are then applied a rolling average of 3 weeks and shifted by 1 week to be predictive of current week.
# Simply put — creates 'rolling_avg' column to show how many points a team has allowed to a position in the last 3 weeks, on average.

year = 2023

def rolling_avg(df):

    # Get rolling average of 3 weeks for each position and each team
    df['rolling_avg'] = df.groupby(['Abbr', 'position'])['Avg'].transform(lambda x: x.rolling(3, min_periods=1).mean())

    # Shift rolling average by 1 week
    df['rolling_avg'] = df.groupby(['Abbr', 'position'])['rolling_avg'].shift(1)

    # Fill nans with 0
    df['rolling_avg'] = df['rolling_avg'].fillna(0)

    return df

ref_key = {
    'QB': 1,
    'RB': 2,
    'WR': 3,
    'TE': 4,
    'K': 5,
    'DST': 6
}

weekly_df = pd.DataFrame()
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=chrome_options)

for week in range(1, 19):
    print(f'Week {week}')
    for position in ref_key.keys():
        if week == 16:
            pass

        url = f"https://fantasy.nfl.com/research/pointsagainst#pointsAgainst=pointsAgainst%2C%2Fresearch%2Fpointsagainst%253Fposition%253D{ref_key[position]}%2526sort%253DpointsAgainst_pts%2526statCategory%253DpointsAgainst%2526statSeason%253D{year}%2526statType%253DweekPointsAgainst%2526statWeek%253D{week}%2Creplace"

        # Get table from url with selenium
        driver.get(url)
        try:
            pos_rank_df = pd.read_html(driver.page_source)[0]
        except:
            break

        # Write to csv
        # pos_rank_df.to_csv(f'cache/def_rankings_{position}_week{week}_{year}.csv', index=False)
        
        # Drop first key of columns
        pos_rank_df.columns = pos_rank_df.columns.droplevel(0)

        # Only keep team and rank cols
        pos_rank_df = pos_rank_df[['Team', 'Avg']]
        
        # For each team name, only keep text before word 'Defense'
        pos_rank_df.loc[:, 'Team'] = pos_rank_df['Team'].apply(lambda x: x.split(' Defense')[0].strip())

        # Get team abbreviation information
        # team_abbr_df = nfl.import_team_desc()[['team_abbr', 'team_name']]
        team_abbr_df = pd.read_csv('cache/team_key.csv')[['team_abbr', 'team_name']]

        pos_rank_df['Abbr'] = pos_rank_df['Team'].apply(lambda x: team_abbr_df[team_abbr_df['team_name'] == x]['team_abbr'].values[0])
        pos_rank_df['week'] = week
        pos_rank_df['position'] = position

        weekly_df = pd.concat([weekly_df, pos_rank_df])

weekly_df = rolling_avg(weekly_df)
weekly_df.to_csv(f'def_rank_cache/def_rankings_{year}.csv', index=False)