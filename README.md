# latam_networks
Visualising conference networks in Latin America

## What this script does
I've taken the Word file of Americanists 1939 conference attendees and put them in a spreadsheet - this lives on the JGI SharePoint.
This script reads that spreadsheet and does the following:
 - Looks at each attendee, and tries to find the location of their origin city
    - If this fails, it tries to find the location of the country's capital city
    - This may make the visualisation a little misleading, but one can indicate on the map whether this has happened if it is a factor
 - Draws a map of the world
 - Draws arrows from each origin point to Lima, where the conference was held. The width of this arrow is proportional to the number of attendees

### How to run
 - Install the requirements
 - Get the required data
    - The script will do most of this for you, but you'll need to put the spreadsheet `americanists_attendees.xlsx` (this can be found on the JGI SharePoint) in the `data/` directory
 - Run `prototype.py`

### Data Sources
City locations lookup table from `https://simplemaps.com/data/world-cities`
