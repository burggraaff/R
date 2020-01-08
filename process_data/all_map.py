import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from astropy.io.ascii import read
from astropy import table
from astropy import units as u
from pathlib import Path

folder = Path("data")

all_data_files = sorted(folder.glob("*processed.tab"))

data = [read(file, include_names=["Latitude", "Longitude"]) for file in all_data_files]
labels = [file.stem[:-10] for file in all_data_files]
colours = ["xkcd:royal blue", "xkcd:orange", "xkcd:lime green", "xkcd:magenta", "xkcd:olive green", "xkcd:navy", "xkcd:maroon", "xkcd:bright pink", "xkcd:hunter green", "xkcd:black", "xkcd:vomit", "xkcd:chocolate", "xkcd:rust brown"]

for tab, label, colour in zip(data, labels, colours):
    tab.add_column(table.Column(name="Label", data=[label for row in tab]))
    tab.add_column(table.Column(name="Colour", data=[colour for row in tab]))

data = table.vstack(data)

# Plot world map
fig = plt.figure(figsize=(8, 5), tight_layout=True)

m = Basemap(projection='moll', lon_0=0, resolution="i")
m.fillcontinents(color="#FFDDCC", lake_color='#DDEEFF')
m.drawmapboundary(fill_color="#DDEEFF")
m.drawcoastlines()

m.drawparallels(np.arange(-90, 95, 15), labels=[1,1,0,0])
m.drawmeridians(np.arange(-180, 180, 30), labels=[0,0,1,1])

m.scatter(data["Longitude"], data["Latitude"], latlon=True, c=data["Colour"], edgecolors="", s=30, zorder=10)

for label, colour in zip(labels, colours):
    m.scatter([0], [0], latlon=True, c=colour, edgecolors="", s=30, zorder=0, label=label)

plt.legend(bbox_to_anchor=(1.1, 1.05))

plt.title(f"Locations of all spectra ($N = {len(data)}$)")

plt.savefig("data/plots/map_all_data.pdf")
plt.show()