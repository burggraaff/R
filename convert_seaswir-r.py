import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from astropy.io.ascii import read
from astropy import table
from astropy import units as u

Ed = read("data/SeaSWIR/SeaSWIR_TRIOS_Ed.tab", data_start=238, header_start=237)

wavelengths = np.arange(350, 902.5, 2.5)

Rrs = read("data/SeaSWIR/SeaSWIR_TRIOS_Rw.tab", data_start=473, format="no_header", delimiter="\t")
colnames = ["Event", "Campaign", "Station", "Location", "Comment (TRIOS missing?)", "Comment (ASD missing?)", "ID", "Latitude", "Longitude", "Date/Time (water sample, UTC)", "Date/Time (TRIOS start, UTC)", "Date/Time (TRIOS end, UTC)", "Ratio (drho/rho, 750nm)", "Ratio (dLsky/Lsky, 750nm)", "Ratio (dLw/Lw, 750nm)", "Ratio (dEd/Ed, 750nm)", "Ratio (d(Lsk/Ed)/(Lsk/Ed), 750nm)"]
colnames_rrs = [f"R_rs_{wvl:.1f}" for wvl in wavelengths]
colnames_rrs2 = [f"R_rs_err_{wvl:.1f}" for wvl in wavelengths]
colnames = colnames + colnames_rrs + colnames_rrs2

for j, newname in enumerate(colnames, 1):
    Rrs.rename_column(f"col{j}", newname)
Rrs.remove_columns(colnames_rrs2)

for wvl in wavelengths:
    if wvl % 1 == 0:
        wvl_raw = f"{wvl:.0f}"
    else:
        wvl_raw = f"{wvl:.1f}"
    Ed.rename_column(f"Ed [mW/m**2/nm] ({wvl_raw} nm)", f"Ed_{wvl:.1f}")
    Ed[f"Ed_{wvl:.1f}"].unit = u.milliwatt / (u.meter**2 * u.nanometer)
    Ed[f"Ed_{wvl:.1f}"] = Ed[f"Ed_{wvl:.1f}"].to(u.watt / (u.meter**2 * u.nanometer))

    Rrs[f"R_rs_{wvl:.1f}"].unit = 1 / u.steradian

combined_table = table.join(Ed, Rrs, keys=["ID"])

for wvl in wavelengths:
    Lw = combined_table[f"R_rs_{wvl:.1f}"] * combined_table[f"Ed_{wvl:.1f}"]
    Lw.name = f"Lw_{wvl}"
    Lw.unit = u.watt / (u.meter**2 * u.nanometer * u.steradian)
    combined_table.add_column(Lw)

R_rs_keys = [key for key in combined_table.keys() if "R_rs" in key]
remove_indices = [i for i, row in enumerate(combined_table) if any(row[key] <= -0.001 for key in R_rs_keys)]
combined_table.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows with negative values")

remove_indices = [i for i, row in enumerate(combined_table) if any(row[key] > 0.1 for key in R_rs_keys)]
combined_table.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows with values > 0.1")

remove_indices = [i for i, row in enumerate(combined_table) if row["R_rs_400.0"] < 0]
combined_table.remove_rows(remove_indices)
print(f"Removed {len(remove_indices)} rows with values of R_rs(400 nm) < 0 or R_rs(800 nm) >= 0.003")

# Plot map of observations
fig = plt.figure(figsize=(5, 10), tight_layout=True)

m = Basemap(projection='merc', lat_0=10, lon_0=-30, llcrnrlon=-60, urcrnrlon=7, llcrnrlat=-38, urcrnrlat=55, resolution="i")
m.fillcontinents(color="#FFDDCC", lake_color='#DDEEFF')
m.drawmapboundary(fill_color="#DDEEFF")
m.drawcoastlines()

m.drawparallels(np.arange(-40, 60, 10), labels=[1,1,0,0])
m.drawmeridians(np.arange(-60, 20, 10), labels=[0,0,1,1])

m.scatter(combined_table["Longitude"], combined_table["Latitude"], latlon=True, c="r", edgecolors="k", s=60, zorder=10)

plt.savefig("map_SeaSWIR-R.pdf")
plt.show()

# Plot all Ed, Lu, Ls, R_rs spectra
fig, axs = plt.subplots(nrows=3, ncols=1, sharex=True, tight_layout=True, gridspec_kw={"wspace":0, "hspace":0})

for row in combined_table:
    spec_Ed = [row[f"Ed_{wvl}"] for wvl in wavelengths]
    spec_Lw = [row[f"Lw_{wvl}"] for wvl in wavelengths]
    spec_R_rs = [row[f"R_rs_{wvl}"] for wvl in wavelengths]

    for ax, spec in zip(axs.ravel(), [spec_Ed, spec_Lw, spec_R_rs]):
        ax.plot(wavelengths, spec, c="k", alpha=0.05, zorder=1)

for ax, label in zip(axs.ravel(), ["$E_d$ [W m$^{-2}$ nm$^{-1}$]", "$L_w$ [W m$^{-2}$ nm$^{-1}$ sr$^{-1}$]", "$R_{rs}$ [sr$^{-1}$]"]):
    ax.set_ylabel(label)
    ax.grid(ls="--", zorder=0)

axs[-1].set_xlabel("Wavelength [nm]")
axs[-1].set_xlim(320, 950)

fig.suptitle(f"SeaSWIR-T spectra ({len(combined_table)})")
plt.savefig("spectra_SeaSWIR-T.pdf")
plt.show()
plt.close()

combined_table.remove_columns(["Event_1", "Event_2", "Campaign_1", "Campaign_2", "Station_1", "Station_2"])
combined_table.write("data/so-p4_processed.tab", format="ascii.fast_tab", overwrite=True)
