import randomPointsGenerator
import this_is_fine.fireHydrantReader as hydrantReader
import caserneReader as stationReader

# Filenames for your CSV data
hydrant_file = "aqu_borneincendie_p.csv"
fire_station_file = "casernes.csv"

def main():
    # 1) Load hydrants
    hydrants = hydrantReader.read_hydrant_data(hydrant_file)

    # 2) Load fire stations
    fire_stations = stationReader.read_fire_stations(fire_station_file)

    # 3) Create a combined hydrant+station map
    stationReader.create_fire_map(hydrants, fire_stations, "fire_map.html")

    # 4) Create a random-points map
    randomPointsGenerator.create_map_with_random_points(n=5, map_filename="montreal_random_points.html")

if __name__ == '__main__':
    main()