import fireHydrantReader as hydrantReader;
import caserneReader as stationReader;
# File paths
hydrant_file = "aqu_borneincendie_p.csv"  # Replace with your actual hydrant CSV file
fire_station_file = "casernes.csv"  # Replace with your actual fire station CSV file

# Load data
def main() :
    hydrants = hydrantReader.read_hydrant_data(hydrant_file)
    fire_stations = stationReader.read_fire_stations(fire_station_file)
    stationReader.create_fire_map(hydrants,fire_stations)
    


if __name__ == '__main__':
    main()