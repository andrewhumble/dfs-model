import pandas as pd

year = 2023
fp_proj_df = pd.DataFrame()

for week in range(1, 19):
    print(f"Getting week {week} projections")
    for position in ['qb', 'rb', 'wr', 'te']:
        url = f"https://www.fantasypros.com/nfl/projections/{position}.php?week={week}&scoring=PPR&year={year}"
        df = pd.read_html(url)[0]
        df = df.droplevel(0, axis=1)

        # Set team col to last word from Player col
        df['team'] = df['Player'].apply(lambda x: x.split()[-1])

        # Remove team from Player col
        df['player_display_name'] = df['Player'].apply(lambda x: ' '.join(x.split()[:-1]))

        df['week'] = week
        df['position'] = position.upper()

        # Rename fp_proj col
        df = df.rename(columns={'FPTS': 'fp_proj'})

        # Drop Player col
        df = df[['player_display_name', 'team', 'week', 'position', 'fp_proj']]

        fp_proj_df = pd.concat([fp_proj_df, df])

fp_proj_df.to_csv(f'fp_proj_cache/fp_proj_{year}.csv', index=False)
print(f"Projections for {year} saved to fp_proj_cache/fp_proj_{year}.csv")