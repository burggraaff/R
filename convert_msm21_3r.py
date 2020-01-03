import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from astropy.io.ascii import read
from astropy import table
from astropy import units as u

Ed = read("data/MSM21_3/MSM21_3_Ed-5nm.tab", data_start=142, header_start=141)
Lu = read("data/MSM21_3/MSM21_3_Lsfc-5nm.tab", data_start=142, header_start=141)
Ls = read("data/MSM21_3/MSM21_3_Lsky-5nm.tab", data_start=141, header_start=140)

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

R_rs_keys = [key for key in combined_table.keys() if "R_rs" in key]
remove_indices = [i for i, row in enumerate(combined_table) if any(row[key] <= -0.001 for key in R_rs_keys)]
combined_table.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows with negative values")

remove_indices = [i for i, row in enumerate(combined_table) if row["R_rs_400"] < 0 or row["R_rs_800"] >= 0.003]
combined_table.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows with values of R_rs(400 nm) < 0 or R_rs(800 nm) >= 0.003")

# Plot map of observations
fig = plt.figure(figsize=(10, 10), tight_layout=True)

m = Basemap(projection='gnom', lat_0=66, lon_0=-40.5, llcrnrlon=-53, urcrnrlon=-12, llcrnrlat=58, urcrnrlat=70.5, resolution="h")
m.fillcontinents(color="#FFDDCC", lake_color='#DDEEFF')
m.drawmapboundary(fill_color="#DDEEFF")
m.drawcoastlines()

m.drawparallels(np.arange(55, 75, 5), labels=[1,1,0,0])
m.drawmeridians(np.arange(-60, -5, 5), labels=[0,0,1,1])

m.scatter(combined_table["Longitude"], combined_table["Latitude"], latlon=True, c="r", edgecolors="k", s=60, zorder=10)

plt.savefig("map_MSM21_3R.pdf")
plt.show()

# Plot all Ed, Lu, Ls, R_rs spectra
fig, axs = plt.subplots(nrows=2, ncols=2, sharex=True, tight_layout=True, gridspec_kw={"wspace":0, "hspace":0})

for row in combined_table:
    spec_Ed = [row[f"Ed_{wvl}"] for wvl in wavelengths]
    spec_Lu = [row[f"Lu_{wvl}"] for wvl in wavelengths]
    spec_Ls = [row[f"Ls_{wvl}"] for wvl in wavelengths]
    spec_R_rs = [row[f"R_rs_{wvl}"] for wvl in wavelengths]

    for ax, spec in zip(axs.ravel(), [spec_Ed, spec_Lu, spec_Ls, spec_R_rs]):
        ax.plot(wavelengths, spec, c="k", alpha=0.05, zorder=1)

for ax, label in zip(axs.ravel(), ["$E_d$ [W m$^{-2}$ nm$^{-1}$]", "$L_u$ [W m$^{-2}$ nm$^{-1}$ sr$^{-1}$]", "$L_s$ [W m$^{-2}$ nm$^{-1}$ sr$^{-1}$]", "$R_{rs}$ [sr$^{-1}$]"]):
    ax.set_ylabel(label)
    ax.grid(ls="--", zorder=0)

axs[0,0].tick_params(bottom=False, labelbottom=False)
axs[0,1].tick_params(bottom=False, labelbottom=False)
axs[0,1].tick_params(left=False, labelleft=False, right=True, labelright=True)
axs[1,1].tick_params(left=False, labelleft=False, right=True, labelright=True)
axs[0,1].yaxis.set_label_position("right")
axs[1,1].yaxis.set_label_position("right")
axs[1,0].set_xlabel("Wavelength [nm]")
axs[1,1].set_xlabel("Wavelength [nm]")
axs[0,0].set_xlim(320, 950)

fig.suptitle(f"MSM21_3R spectra ({len(combined_table)})")
plt.savefig("spectra_MSM21_3R.pdf")
plt.show()
plt.close()

combined_table.remove_columns(["Latitude_1", "Longitude_1", "Altitude [m]_1", "Latitude_2", "Longitude_2", "Altitude [m]_2"])
combined_table.write("data/msm21_3r_processed.tab", format="ascii.fast_tab", overwrite=True)