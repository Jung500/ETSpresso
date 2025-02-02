#!/usr/bin/env python3
"""
generate_severity_data.py
Generates synthetic data for a "fire severity" ML model.
Creates fire_severity_data.csv in the scripts folder.
"""

import csv
import random

def main():
    # The column headers
    header = ["lat", "lon", "dist_station", "time_of_day", "severity"]

    with open("fire_severity_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for _ in range(300):
            # Generate a random lat/lon around Montreal ~ [45.50..45.60] x [-73.60..-73.50]
            lat = 45.50 + random.random() * 0.1
            lon = -73.60 + random.random() * 0.1

            # random distance to station, say 100m to 5000m
            dist_station = random.uniform(100, 5000)

            # random hour of day [0..23]
            time_of_day = random.randint(0, 23)

            # compute a "base" to pick severity
            # larger dist + later time => higher severity
            base = dist_station * 0.001 + time_of_day * 0.02 + random.random() * 2

            if base < 5:
                label = "low"
            elif base < 9:
                label = "medium"
            else:
                label = "high"

            # write one row
            writer.writerow([lat, lon, dist_station, time_of_day, label])

    print("fire_severity_data.csv created with 300 rows.")

if __name__ == "__main__":
    main()