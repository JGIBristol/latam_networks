# latam_networks
Visualising conference networks in Latin America

## What this script does
I've taken the Word file of Americanists 1939 conference attendees and put them in a spreadsheet - this lives on the JGI SharePoint.
This script reads that spreadsheet and does the following:
 - Looks at each attendee and finds the location of their origin city
 - Draws a map of the world
 - Draws arrows from each origin point to Lima, where the conference was held. The width of this arrow is proportional to the number of attendees

### How to run
 - Install the requirements
 - Get the required data
    - The script will do most of this for you, but you'll need to put the spreadsheet `americanists_attendees.xlsx` (this can be found on the JGI SharePoint) in the `data/` directory
 - Run `prototype.py`

### Data Sources
City locations lookup table from `https://simplemaps.com/data/world-cities`
This is a modern map of the world so might not match up to the 1939 borders, but it should be good enough for our visualisations
