#%%
from processing.data import create_data
from analysis.predict import predict
import pandas as pd

week = 5
year = 2023

df = create_data(year, week)
df.to_csv(f"data/weekly_compiled/week{week}_{year}_compiled.csv")

df, rmse = predict(df)
df.to_csv(f'data/cache/weekly_{year}_projections.csv')
# %%
