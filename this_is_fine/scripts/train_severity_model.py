#!/usr/bin/env python3
"""
train_severity_model.py
Trains a scikit-learn RandomForestClassifier 
on fire_severity_data.csv, 
then saves the model to severity_model.pkl.
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def main():
    # Load the CSV produced by generate_severity_data.py
    df = pd.read_csv("fire_severity_data.csv")

    # We'll treat lat, lon, dist_station, time_of_day as X
    X = df[["lat", "lon", "dist_station", "time_of_day"]]
    # The "severity" column is y
    y = df["severity"]

    # Create/Train a random forest
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)

    # Save model
    joblib.dump(model, "severity_model.pkl")
    print("Trained model saved to severity_model.pkl")

if __name__ == "__main__":
    main()