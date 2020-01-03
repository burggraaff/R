"""
Generate boxcar and gaussian spectral response functions
"""

from bandaveraging import load_data, bandaverage_multi, boxplot_absolute, boxplot_relative
import response_curves as rc

wavelengths_data, Ed, Lw, R_rs = load_data()

for func in [rc.load_Sentinel2A, rc.load_Sentinel2B]:
    sensor = func()
    sensor.plot()

    reflectance_space = sensor.band_average(wavelengths_data, R_rs)
    radiance_space = sensor.band_average(wavelengths_data, Lw) / sensor.band_average(wavelengths_data, Ed)
    difference_absolute = reflectance_space - radiance_space
    difference_relative = 100*difference_absolute / radiance_space

    sensor.boxplot_relative(difference_relative)
    sensor.boxplot_absolute(difference_absolute)