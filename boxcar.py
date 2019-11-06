"""
Generate boxcar and gaussian spectral response functions
"""

import numpy as np
from matplotlib import pyplot as plt
from astropy.io.ascii import read
from astropy import table
from mpl_toolkits.axes_grid1 import make_axes_locatable
from bandaveraging import split_spectrum, bandaverage_multi

wavelengths_band = np.arange(320, 800, 0.1)

wavelengths_central = np.arange(350, 780, 3)
FWHMs = np.arange(1, 75, 1)

boxcar_result = np.tile(np.nan, [len(FWHMs), len(wavelengths_central)])

wavelengths_interp = np.arange(380, 800.5, 0.5)

def generate_boxcar(x, center, fwhm):
    response = np.zeros_like(x)
    response[np.abs(x - center) <= fwhm/2] = 1.
    return response

data_norcohab = read("data/norcohab_processed.tab")
data_archemhab = read("data/archemhab_processed.tab")

data_all = table.vstack([data_norcohab, data_archemhab])

wavelengths, Ed = split_spectrum(data_all, "Ed")
wavelengths, Lw = split_spectrum(data_all, "Lw")
wavelengths, R_rs = split_spectrum(data_all, "R_rs")

for i,center in enumerate(wavelengths_central):
    for j,fwhm in enumerate(FWHMs):

        # Boxcar
        if center-fwhm/2 < wavelengths_band[0] or center+fwhm/2 > wavelengths_band[-1]:
            # Skip combination if the boxcar response does not fall entirely
            # within the data wavelength range
            continue
        boxcar_response = generate_boxcar(wavelengths_band, center, fwhm)
        boxcar_reflectance_space = bandaverage_multi(wavelengths_band, boxcar_response, wavelengths, R_rs)
        boxcar_radiance_space = bandaverage_multi(wavelengths_band, boxcar_response, wavelengths, Lw) / bandaverage_multi(wavelengths_band, boxcar_response, wavelengths, Ed)
        boxcar_result[j,i] = np.median((boxcar_radiance_space - boxcar_reflectance_space) / boxcar_radiance_space)

# imshow plots
im = plt.imshow(100*boxcar_result, origin="lower", extent=[wavelengths_central[0], wavelengths_central[-1], FWHMs[0], FWHMs[-1]], aspect="auto")
plt.xlabel("Central wavelength [nm]")
plt.ylabel("FWHM [nm]")
divider = make_axes_locatable(plt.gca())
cax = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(im, cax=cax)
cax.set_ylabel("Difference (Rad. space - Refl. space, %)")
plt.show()

# contourf plots
im = plt.contourf(100*boxcar_result, origin="lower", extent=[wavelengths_central[0], wavelengths_central[-1], FWHMs[0], FWHMs[-1]], aspect="auto")
plt.xlabel("Central wavelength [nm]")
plt.ylabel("FWHM [nm]")
divider = make_axes_locatable(plt.gca())
cax = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(im, cax=cax)
cax.set_ylabel("Difference (Rad. space - Refl. space, %)")
plt.show()
