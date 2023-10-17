from analysis.predict import predict 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

week = 6
year = 2023

df = pd.read_csv(f'data/predictions/week{week}_{year}.csv')

# Convert dummmy cols back to single col
df['position'] = df[['position_QB', 'position_RB', 'position_TE', 'position_WR']].idxmax(axis=1).str.replace('position_', '')

# Make player rankings by prediction value for each position for a given week
qb_rankings = df[(df['position'] == 'QB') & (df['week'] == week)].sort_values('prediction', ascending=False).reset_index(drop=True)
qb_rankings['rank'] = qb_rankings.index + 1
rb_rankings = df[(df['position'] == 'RB') & (df['week'] == week)].sort_values('prediction', ascending=False).reset_index(drop=True)
rb_rankings['rank'] = rb_rankings.index + 1
wr_rankings = df[(df['position'] == 'WR') & (df['week'] == week)].sort_values('prediction', ascending=False).reset_index(drop=True)
wr_rankings['rank'] = wr_rankings.index + 1
te_rankings = df[(df['position'] == 'TE') & (df['week'] == week)].sort_values('prediction', ascending=False).reset_index(drop=True)
te_rankings['rank'] = te_rankings.index + 1

# Drop QBs with a prediction lower than 10
qb_rankings = qb_rankings[qb_rankings['prediction'] > 10]

# Drop RBs with a prediction lower than 5
rb_rankings = rb_rankings[rb_rankings['prediction'] > 5]

# Drop WRs with a prediction lower than 5
wr_rankings = wr_rankings[wr_rankings['prediction'] > 5]

# Drop TEs with a prediction lower than 5
te_rankings = te_rankings[te_rankings['prediction'] > 5]

# Loop through zip file of player rankings by position
for rankings in zip([qb_rankings, rb_rankings, wr_rankings, te_rankings], ['QB', 'RB', 'WR', 'TE']):
    with open(f"data/rankings/{rankings[1].lower()}_rankings.csv", 'w') as f:
        f.write(rankings[0].to_csv(index=False))
    with open(f'/Users/andrewhumble/HumbleDFS/humbledfs.github.io/_includes/{rankings[1].lower()}_rankings.html', 'w') as f:
        f.write(rankings[0][['rank', 'player_display_name', 'recent_team', 'opponent', 'prediction', 'actual', 'error']].to_html(index=False, border=0))
