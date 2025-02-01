import csv

# Define the file path
file_path = "your_file.csv"  # Replace with your actual file path

# Open and read the file
with open(file_path, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file)  # Reads file as a dictionary with column headers as keys
    
    for row in reader:
        filtered_data = {
            "Address": row["ADRESSE"],
            "Jurisdiction": row["JURIDICTION"],
            "Owner": row["PROPRIETAIRE"],
            "Installation Date": row["DATE_INSTALLATION"],
            "Status": row["STATUT_ACTIF"],
            "Abandoned": row["ABANDONNE_R"],
            "Date of Abondon": row['DATE_ABANDON'],
            "Installation Data Source": row["PROVENANCE_DONNEE"],
            "Elevation (Terrain Level)": row["ELEVATION_TERRAIN"],
            "Spatial Coordinates (X, Y)": f"{row['COORDONNEE_SPATIALE_X']}, {row['COORDONNEE_SPATIALE_Y']}",
            "Latitude / Longitude": f"{row['LATITUDE']}, {row['LONGITUDE']}",
            "Data Source": row["PROVENANCE_DONNEE"]
        }
        print(filtered_data)  # Process as needed