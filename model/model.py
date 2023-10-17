import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import pickle

def get_model():
    # Load the data
    df = pd.read_csv('data/train.csv')

    # Make index the player name and week
    df = df.set_index(['player_display_name', 'season', 'week'])

    # Case index dtype to object
    df.index = df.index.astype('object')

    # Replace nan values with 0
    df = df.fillna(0)

    # Select features
    features = df.select_dtypes("number").columns

    # Take out numerical columns that aren't features
    # fp_proj included for now
    features = features.drop(['fantasy_points', 'fantasy_points_ppr'])

    X_train, X_test, y_train, y_test = train_test_split(df[features], df['fantasy_points_ppr'], test_size=0.33, random_state=42)

    model = RandomForestRegressor()
    model.fit(X_train, y_train)

    # Make predictions
    predictions = model.predict(X_test)

    rmse = np.sqrt(np.mean((predictions - y_test)**2))

    print(rmse)

    # Output model to file
    with open('model/model.pkl', 'wb') as f:
        pickle.dump(model, f)

    return X_test, y_test, X_train, y_train, model, predictions, features

if __name__ == '__main__':
    get_model()