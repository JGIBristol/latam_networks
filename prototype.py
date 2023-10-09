"""
Prototype visualisation for one conference only

"""
import os
import sys
import zipfile
import warnings
import urllib.request

import yaml
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib

# This is basically just to make my thing work on WSL
matplotlib.use("Agg")


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


def add_lat_long(data: pd.DataFrame) -> None:
    """
    Get the latitude and longitude for each entry in the data; adds it to the dataframe in place

    This will first try to get the location of each city; if this isn't possible, raise AssertionError

    This doesn't deal with the case where two cities have the same name but are in different countries...
    but I don't think that has happened...

    """
    # Download the table of city locations if not already downloaded
    city_locations = get_city_locations()

    # Empty columns in the dataframe to store latitude and longitude
    data["lat"] = np.ones(len(data)) * np.nan
    data["lng"] = np.ones(len(data)) * np.nan

    # For each city look up latitude and longitude
    for city in set(data["City"]):
        # Special cases where we can't assume the right city is the first one (i.e. the largest)
        if city == "Cambridge, Mass.":
            # Need a different query
            city_df = city_locations.query(f"city_ascii=='Cambridge'")

            city_df = city_df.iloc[
                [2]
            ]  # The right one is the third largest (Cananda, UK, US)

        elif city == "San Jose":
            city_df = city_locations.query(f"city_ascii=='{city}'")
            city_df = city_df.iloc[[1]]  # The right one is second (US, Costa Rica)

        elif city == "Concepcion":
            city_df = city_locations.query(f"city_ascii=='{city}'")
            city_df = city_df.iloc[[5]]  # I think this one is right...

        else:
            # Get a slice of the dataframe containing our city of interest
            city_df = city_locations.query(f"city_ascii=='{city}'")

            # There might be more than one city with the same name (e.g. there's a Lima in Ohio...)
            # Emit a warning if this is the case
            if len(city_df) > 1:
                warnings.warn(
                    f"\n\x1b[33;1m More than one city found: check that the first entry here is the desired '{city}' \x1b[0m\n"
                )
                print(city_df, file=sys.stderr)

                city_df = city_df.head(1)

        # Something weird might have happened
        if len(city_df) == 0:
            raise AssertionError(f"\x1b[31;1m Need a special case for {city}\x1b[0m")

        lat = city_df["lat"].iloc[0]
        lng = city_df["lng"].iloc[0]

        # Add the latitude and longitude to all the rows with this city
        keep = data["City"] == city
        data.loc[keep, "lat"] = lat
        data.loc[keep, "lng"] = lng


def get_shapefile() -> gpd.GeoDataFrame:
    """
    Download if necessary and return the shapefile for the world

    """
    path = "data/world_shapefile.json"
    if not os.path.exists(path):
        urllib.request.urlretrieve(config()["world_shapefile_url"], path)

    return gpd.read_file(path, driver="GeoJSON", epsg=4326)


def main():
    """
    Read in and clean the data and make a basic visualisation suitable as a proof-of-concept

    """
    data = read_data()
    print(data)

    # Clean the data
    data["City"] = data["City"].str.strip()
    print(set(data["City"]))

    # Get the latitude/longitude for each entry
    add_lat_long(data)

    # Get + plot a shapefile for the world
    fig, axes = plt.subplot_mosaic("AAA\nAAA\nBBC\nBBC", figsize=(10, 8))
    world_geodf = get_shapefile()
    world_geodf.plot(ax=axes["A"])

    # Draw an arrow from the origin point to Lima (where the conference took place)
    lima_coords = -77.0375, -12.06
    for _, row in data.iterrows():
        lat, lng = row["lat"], row["lng"]

        dx = lng - lima_coords[0]
        dy = lat - lima_coords[1]

        axes["A"].arrow(*lima_coords, dx, dy)

    # Change axis limits of map
    xlim = (-180, 180)
    ylim = (-55, 90)
    axes["A"].set_xlim(xlim)
    axes["A"].set_ylim(ylim)

    axes["A"].set_axis_off()

    fig.tight_layout()
    fig.savefig("world.png")


if __name__ == "__main__":
    main()
