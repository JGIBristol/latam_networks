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
from matplotlib.patches import Circle

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


def gender_plot(axis: plt.Axes, gender: pd.Series) -> None:
    """
    Plot a chart showing the proportion of men/women on an axis

    :param axis: The axis to plot on
    :param gender: Series holding Y for women and NaN for men

    """
    assert set(gender) == {"Y", np.nan}

    # Assumes there's more men than women, which is the case here
    n_men, n_women = gender.value_counts(dropna=False)

    # Plot them as black and purple wedges
    axis.pie(
        [n_men, n_women],
        explode=[0.0, 0.15],
        colors=["black", "purple"],
        counterclock=False,
        labels=["$\u2642$", "$\u2640$"],
        labeldistance=0.5,
        textprops={"color": "white", "fontsize": 24},
    )


def plot_map(axis: plt.Axes, data: pd.DataFrame, *, scale: float = 1.0) -> None:
    """
    Plot a map of the world on an axis with some arrows and patches on it

    """
    world_geodf = get_shapefile()
    world_geodf.plot(ax=axis, color="white", edgecolor="black", linewidth=0.5)

    # Draw an arrow from the origin point to Lima (where the conference took place)
    lima_coords = -77.0375, -12.06
    city_lookup = data[["City", "lat", "lng"]].drop_duplicates()
    city_lookup.reset_index(inplace=True)
    city_lookup["n_attendees"] = np.ones(len(city_lookup)) * np.nan

    for i, city, lat, lng in zip(
        city_lookup.index, city_lookup["City"], city_lookup["lat"], city_lookup["lng"]
    ):
        # Find how many there are
        n_travellers = len(data.query(f"lat=={lat} and lng=={lng}"))
        city_lookup["n_attendees"].iloc[i] = n_travellers

        # Draw a faded out circle showing how many attendees there were in each city
        # Don't do this for Lima, since it obscures the others
        if city != "Lima":
            patch = Circle(
                (lng, lat),
                radius=np.sqrt(n_travellers) * scale,
                alpha=0.5,
                facecolor="r",
                edgecolor="none",
            )
        else:
            patch = Circle(
                (lng, lat),
                radius=np.sqrt(n_travellers) * scale,
                facecolor="green",
                alpha=0.6,
            )

        axis.add_patch(patch)

        dx = lng - lima_coords[0]
        dy = lat - lima_coords[1]

        axis.arrow(*lima_coords, dx, dy, width=0.001 * n_travellers, alpha=0.6)

    return city_lookup


def world_map_plot(axis: plt.Axes, data: pd.DataFrame) -> None:
    """
    Plot a map of the world indicating where the delegates came from

    :param axis: axis to plot on
    :param data: dataframe holding countr

    """
    city_lookup = plot_map(axis, data)

    city_lookup.sort_values("n_attendees", inplace=True, ascending=False)
    for i, row in city_lookup.head(8).reset_index().iterrows():
        x, y = -180, -5 * i
        axis.text(x, 8, "Most Delegates")
        axis.text(
            x,
            y,
            f"{row['City']:<19}{int(row['n_attendees'])}",
            font="FreeMono",
        )

        offset = 56
        if row["City"] != "Lima":
            patch = Circle(
                (x + offset, y + 1.5),
                radius=np.sqrt(row["n_attendees"]),
                alpha=0.5,
                facecolor="r",
                edgecolor="none",
            )
        else:
            patch = Circle(
                (x + offset, y + 1.5),
                radius=np.sqrt(row["n_attendees"]),
                facecolor="green",
                alpha=0.6,
            )
        axis.add_patch(patch)

    # Change axis limits of map
    xlim = (-180, 180)
    ylim = (-55, 90)
    axis.set_xlim(xlim)
    axis.set_ylim(ylim)

    axis.set_axis_off()


def sa_map_plot(axis: plt.Axes, data: pd.DataFrame) -> None:
    """
    Plot a map of the south american contributions

    """
    sa_countries = [
        "Peru",
        "Argentina",
        "Mexico",
        "Uruguay",
        "Brazil",
        "Chile",
        "Bolivia",
        "Ecuador",
    ]

    sa_data = data[data["Country"].str.strip(" .").isin(sa_countries)]

    plot_map(axis, sa_data, scale=0.8)

    axis.set_xlim(-110, -30)
    axis.set_ylim(-60, 30)

    axis.set_axis_off()


def peru_map_plot(axis: plt.Axes, data: pd.DataFrame) -> None:
    """
    Plot a map of the south american contributions

    """
    peru_data = data[data["Country"].str.strip(" .").isin(["Peru"])]

    plot_map(axis, peru_data, scale=0.2)

    peru_data = peru_data.drop_duplicates("City")[["City", "lat", "lng"]]

    # Do these automatically
    auto = ["Trujillo", "Huaraz", "Quillabamba", "Cusco", "Arequipa", "Tacna", "Puno"]
    for _, row in peru_data.iterrows():
        if row["City"] in auto:
            axis.text(
                row["lng"] + 0.2, row["lat"], row["City"], font="FreeMono", fontsize=8
            )

    print(peru_data)
    # Do these ones manually
    axis.text(-77.1, -14.7, "Ica", font="FreeMono", fontsize=8)

    axis.set_xlim(-85, -67)
    axis.set_ylim(-20, 1)

    axis.set_axis_off()


def main():
    """
    Read in and clean the data and make a basic visualisation suitable as a proof-of-concept

    """
    data = read_data()

    # Clean the data
    data["City"] = data["City"].str.strip()

    # Get the latitude/longitude for each entry
    add_lat_long(data)

    fig, axes = plt.subplot_mosaic("AAA\nAAA\nBCD\nBCD", figsize=(10, 8))

    # Get + plot a shapefile for the world
    world_map_plot(axes["A"], data)

    sa_map_plot(axes["B"], data)

    peru_map_plot(axes["C"], data)

    # Plot a chart showing genders
    gender_plot(axes["D"], data["Female"])

    fig.suptitle(
        "XXVII INTERNATIONAL CONGRESS OF AMERICANISTS\nLIMA, 1939", weight="bold"
    )

    fig.tight_layout()
    fig.savefig("world.svg")


if __name__ == "__main__":
    main()
