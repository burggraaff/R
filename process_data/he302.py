import numpy as np
from astropy import table
from astropy import units as u
from sba.plotting import plot_spectra, map_data
from sba.io import read, write_data
from sba.data_processing import convert_to_unit

Ed = read("data/HE302/HE302_irrad.tab", data_start=186, header_start=185)
Rrs = read("data/HE302/HE302_rrs.tab", data_start=186, header_start=185)

wavelengths = np.arange(320, 955, 5)
for wvl in wavelengths:
    Ed_k, R_rs_k = f"Ed_{wvl}", f"R_rs_{wvl}"
    Ed.rename_column(f"Ed_{wvl} [W/m**2/nm]", Ed_k)
    convert_to_unit(Ed, Ed_k, u.watt / (u.meter**2 * u.nanometer))

    Rrs.rename_column(f"Rrs_{wvl} [1/sr]", R_rs_k)
    convert_to_unit(Rrs, R_rs_k, 1 / u.steradian)

data = table.join(Ed, Rrs, keys=["Event"])

for wvl in wavelengths:
    Lw = data[f"Ed_{wvl}"] * data[f"R_rs_{wvl}"]
    Lw.name = f"Lw_{wvl}"
    Lw.unit = u.watt / (u.meter**2 * u.nanometer * u.steradian)
    data.add_column(Lw)

remove_indices = [i for i, row in enumerate(data) if row["R_rs_800"] >= 0.003]
data.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows with values of R_rs(800 nm) >= 0.003")

for key in ["Date/Time", "Latitude", "Longitude", "Altitude [m]"]:
    data.rename_column(f"{key}_1", key)
    data.remove_column(f"{key}_2")

map_data(data, data_label="HE302", projection='gnom', lat_0=55, lon_0=0, llcrnrlon=-10, urcrnrlon=11, llcrnrlat=50.5, urcrnrlat=59.5, resolution="h", parallels=np.arange(40, 70, 2), meridians=np.arange(-20, 20, 2))

plot_spectra(data, data_label="HE302", alpha=0.15)

write_data(data, label="HE302")
