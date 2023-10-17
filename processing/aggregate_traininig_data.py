import pandas as pd
import nfl_data_py as nfl

df0 = pd.read_csv('data/2019.csv')
df1 = pd.read_csv('data/2020.csv')
df2 = pd.read_csv('data/2021.csv')
# df3 = pd.read_csv('data/2022.csv')

combined = pd.concat([df0, df1, df2])

combined.to_csv('data/train.csv', index=False)