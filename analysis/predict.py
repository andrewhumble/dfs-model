import pickle
import pandas as pd

def predict(data):
    rf_model = pickle.load(open('model/model.pkl', 'rb'))

    # Load 2022 data
    new_data = data
    new_data = new_data.fillna(0)

    # Select features
    features = new_data.select_dtypes("number").columns

    # Take out numerical columns that aren't features
    features = features.drop(['week', 'season', 'fantasy_points', 'fantasy_points_ppr'])

    # Make predictions on the new data
    predictions = rf_model.predict(new_data[features])
    new_data['prediction'] = predictions

    # Rename fantasy_points_ppr to actual
    new_data = new_data.rename(columns={'fantasy_points_ppr': 'actual'})

    # Add error column
    new_data['error'] = new_data['prediction'] - new_data['actual']

    new_data['change_in_prediction'] = new_data.groupby('player_id')['prediction'].diff()

    # Calc rmse
    rmse =  ((new_data['error'] ** 2).mean() ** .5)

    return new_data, rmse
