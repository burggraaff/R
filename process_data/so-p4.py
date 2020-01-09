import numpy as np
from astropy import table
from astropy import units as u
from sba.plotting import plot_spectra, map_data
from sba.io import read, write_data

Ed = read("data/SO-P4/SO-P4_irrad.tab", data_start=142, header_start=141)
Lu = read("data/SO-P4/SO-P4_rad_up_40deg.tab", data_start=142, header_start=141)
Ls = read("data/SO-P4/SO-P4_sky_rad_40deg.tab", data_start=142, header_start=141)

wavelengths = np.arange(320, 955, 5)
for wvl in wavelengths:
    Ed.rename_column(f"Ed_{wvl} [W/m**2/nm]", f"Ed_{wvl}")
    Ed[f"Ed_{wvl}"].unit = u.watt / (u.meter**2 * u.nanometer)

    try:  # mu gets properly loaded on Linux
        Lu.rename_column(f"Lu_{wvl} [µW/cm**2/nm/sr]", f"Lu_{wvl}")
    except KeyError: # but not on Windows
        Lu.rename_column(f"Lu_{wvl} [ÂµW/cm**2/nm/sr]", f"Lu_{wvl}")
    Lu[f"Lu_{wvl}"].unit = u.microwatt / (u.centimeter**2 * u.nanometer * u.steradian)
    Lu[f"Lu_{wvl}"] = Lu[f"Lu_{wvl}"].to(u.watt / (u.meter**2 * u.nanometer * u.steradian))

    Ls.rename_column(f"Ls_{wvl} [W/m**2/nm/sr]", f"Ls_{wvl}")
    Ls[f"Ls_{wvl}"].unit = u.watt / (u.meter**2 * u.nanometer * u.steradian)

combined_table = table.join(Ed, Lu, keys=["Date/Time"])
combined_table = table.join(combined_table, Ls, keys=["Date/Time"])

for wvl in wavelengths:
    Lw = combined_table[f"Lu_{wvl}"] - 0.028 * combined_table[f"Ls_{wvl}"]
    Lw.name = f"Lw_{wvl}"
    combined_table.add_column(Lw)
    R_rs = combined_table[f"Lw_{wvl}"] / combined_table[f"Ed_{wvl}"]
    R_rs.name = f"R_rs_{wvl}"
    R_rs.unit = 1 / u.steradian
    combined_table.add_column(R_rs)

# Normalise by R_rs(750 nm), re-calculate Lw
normalisation = combined_table["R_rs_750"].copy()
for wvl in wavelengths:
    combined_table[f"R_rs_{wvl}"] = combined_table[f"R_rs_{wvl}"] - normalisation
    combined_table[f"Lw_{wvl}"] = combined_table[f"R_rs_{wvl}"] * combined_table[f"Ed_{wvl}"]

# Remove rows where Ed_405 is abnormally low compared to Ed_400
diff = combined_table["Ed_400"] - combined_table["Ed_405"]
remove_indices = [i for i, row in enumerate(combined_table) if diff[i] > 0.15]
combined_table.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows where Ed(400 nm) - Ed(405 nm) > 0.15")

# Remote rows with spiky R_rs
R_rs_keys = [key for key in combined_table.keys() if "R_rs" in key]
remove_indices = [i for i, row in enumerate(combined_table) if any([np.abs(row[key1]-row[key2]) >= 0.002 for key1, key2 in zip(R_rs_keys, R_rs_keys[1:])])]
combined_table.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows with differences in R_rs >=0.002 between wavelengths")

# Remove rows with negative R_rs
remove_indices = [i for i, row in enumerate(combined_table) if any(row[key] < -0.001 for key in R_rs_keys)]
combined_table.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows with negative values")

# Remove columns that are consistently negative in R_rs
for wvl in wavelengths[(wavelengths < 375) | (wavelengths > 700)]:
    remove_keys = [f"{s}_{wvl:.0f}" for s in ("Ed", "Lw", "R_rs")]
    combined_table.remove_columns(remove_keys)

map_data(combined_table, data_label="SO-P4", projection='gnom', lat_0=56, lon_0=5, llcrnrlon=-2, urcrnrlon=11, llcrnrlat=52, urcrnrlat=59, resolution="h", parallels=np.arange(40, 70, 2), meridians=np.arange(-20, 20, 2))

plot_spectra(combined_table, data_label="SO-P4", alpha=0.05)

combined_table.remove_columns(["Latitude_1", "Longitude_1", "Altitude [m]_1", "Latitude_2", "Longitude_2", "Altitude [m]_2"])
write_data(combined_table, "SO-P4")