"""
Prototype visualisation for one conference only

"""
import os
import zipfile
import urllib.request

import yaml
import pandas as pd


def config() -> dict:
    """
    Read the configuration file

    """
    with open("config.yml", "r") as yaml_f:
        return yaml.safe_load(yaml_f)


def read_data() -> pd.DataFrame:
    """
    Read in the data from the excel file in data/

    """
    # I created a symlink to my OneDrive, but you could copy the into the data/ directory
    return pd.read_excel("data/americanists_attendees.xlsx", sheet_name="Tabelle1")


def get_city_locations() -> pd.DataFrame:
    """
    Download + unzip the table of city locations if required, then read + return it as a dataframe

    """
    # Download it
    if not os.path.exists("data/city_locations.zip"):
        urllib.request.urlretrieve(
            config()["city_locations_url"], "data/city_locations.zip"
        )

    # Extract the spreadsheet
    if not os.path.exists("data/worldcities.csv"):
        with zipfile.ZipFile("data/city_locations.zip") as zf:
            zf.extract("worldcities.csv", "data/")

    # Open the right spreadsheet
    return pd.read_csv("data/worldcities.csv")


def get_lat_long(data: pd.DataFrame) -> tuple:
    """
    Get the latitude and longitude for each entry in the data

    This will first try to get the location of each city; if this isn't possible, it will try to get the location of the country

    If this also fails it will enter NaN

    """
    # Download the table of city locations if not already downloaded
    city_locations = get_city_locations()
    print(city_locations)

    # For each city look up latitude and longitude

    # If it isn't found, try finding the country's capital

    # If this still isn't found, enter NaN


def main():
    """
    Read in and clean the data and make a basic visualisation suitable as a proof-of-concept

    """
    data = read_data()

    # Clean the data
    data["City"] = data["City"].str.strip()

    # Get the latitude/longitude for each entry
    latitudes, longitudes = get_lat_long(data)
    data["lat"] = latitudes
    data["long"] = longitudes

    # Get + plot a shapefile for the world

    # On the shapefile, draw an arrow from the origin point to Lima (where the conference took place)


if __name__ == "__main__":
    main()
