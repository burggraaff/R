import numpy as np
from astropy import table
from astropy import units as u
from pathlib import Path
from sba.plotting import plot_spectra, map_data
from sba.io import read, write_data, find_auxiliary_information_seabass
from sba.data_processing import get_keys_with_label, remove_negative_R_rs, remove_rows_based_on_threshold

folder = Path("data/ORINOCO/")
files = sorted(folder.glob("*.txt"))

tabs = []
for file in files:
    for skiprows in range(40, 52):
        try:
            wavelengths, Ed, Rrs = np.loadtxt(file, skiprows=skiprows, unpack=True, usecols=[0,3,5])
        except Exception:
            continue
        else:
            break

    date, time, lon, lat = find_auxiliary_information_seabass(file)

    cols = ["Date", "Time", "Latitude", "Longitude"] + [f"Ed_{wvl:.0f}" for wvl in wavelengths] + [f"R_rs_{wvl:.0f}" for wvl in wavelengths]
    dtype = [int, "S8", float, float] + 2 * [float for wvl in wavelengths]
    tab = table.Table(rows=[[date, time, lat, lon, *Ed, *Rrs]], names=cols, dtype=dtype)
    tabs.append(tab)

data = table.vstack(tabs)

Ed_keys, R_rs_keys = get_keys_with_label(data, "Ed", "R_rs")

for Ed_k, R_rs_k in zip(Ed_keys, R_rs_keys):
    wavelength = int(Ed_k[3:])

    data[Ed_k].unit = u.microwatt / (u.cm**2 * u.nm)
    data[Ed_k] = data[Ed_k].to(u.watt / (u.m**2 * u.nm))

    data[R_rs_k].unit = 1 / u.steradian

    Lw = data[f"Ed_{wavelength}"] * data[f"R_rs_{wavelength}"]
    Lw.name = f"Lw_{wavelength}"
    Lw.unit = u.watt / (u.m**2 * u.nm * u.steradian)
    data.add_column(Lw)

remove_negative_R_rs(data)

map_data(data, data_label="ORINOCO", projection='gnom', lat_0=10.5, lon_0=-64.67, llcrnrlon=-70, urcrnrlon=-59, llcrnrlat=5, urcrnrlat=15, resolution="h", parallels=np.arange(4, 16, 2), meridians=np.arange(-70, -56, 2))

plot_spectra(data, data_label="ORINOCO", alpha=0.1)

write_data(data, label="ORINOCO")