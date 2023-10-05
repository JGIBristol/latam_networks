"""
Prototype visualisation for one conference only

"""
import pandas as pd


def read_data() -> pd.DataFrame:
    """
    Read in the data from the excel file in data/

    """
    # I created a symlink to my OneDrive, but you could copy the into the data/ directory
    return pd.read_excel("data/americanists_attendees.xlsx", sheet_name="Tabelle1")


def main():
    """
    Read in and clean the data and make a basic visualisation suitable as a proof-of-concept

    """
    data = read_data()

    # Clean the data
    data["City"] = data["City"].str.strip()

    # See which cities we have


if __name__ == "__main__":
    main()
