"""
Module with functions for band-averaging
"""

import numpy as np
from matplotlib import pyplot as plt
from astropy.io.ascii import read
from astropy import table
import sys

def split_spectrum(data_table, label):
    keys_relevant = [key for key in data_table.keys() if label in key]
    wavelengths = np.array([float(key.split("_")[-1]) for key in keys_relevant])
    try:
        spectra = np.array([data_table[key]._data for key in keys_relevant]).T
    except AttributeError:
        spectra = np.array([data_table[key].data for key in keys_relevant]).T
    return wavelengths, spectra

def bandaverage(band_wavelengths, band_response, data_wavelengths, data_response):
    response_interpolated = np.interp(band_wavelengths, data_wavelengths, data_response, left=0, right=0)
    response_multiplied = response_interpolated * band_response
    response_sum = np.trapz(response_multiplied, x=band_wavelengths)
    weight_sum = np.trapz(band_response, x=band_wavelengths)
    response_average = response_sum / weight_sum
    return response_average

def bandaverage_multi(band_wavelengths, band_response, data_wavelengths, data_response_multi):
    response_interpolated = np.array([np.interp(band_wavelengths, data_wavelengths, data_response, left=0, right=0) for data_response in data_response_multi])
    response_multiplied = response_interpolated * band_response
    response_sum = np.trapz(response_multiplied, x=band_wavelengths, axis=1)
    weight_sum = np.trapz(band_response, x=band_wavelengths)
    response_average = response_sum / weight_sum
    return response_average

def calculate_differences(reflectance_space, radiance_space):
    difference_absolute = reflectance_space - radiance_space
    difference_relative = 100 * difference_absolute / radiance_space

    return difference_absolute, difference_relative

def calculate_median_and_errors(differences):
    lower_percentile = np.nanpercentile(differences, 15.9, axis=1)
    medians = np.nanmedian(differences, axis=1)
    upper_percentile = np.nanpercentile(differences, 84.1, axis=1)
    lower_error = medians - lower_percentile
    upper_error = upper_percentile - medians
    return medians, lower_error, upper_error

def load_data_full():
    data_all = read(sys.argv[1])
    return data_all

def load_data():
    data_all = load_data_full()

    wavelengths, Ed = split_spectrum(data_all, "Ed")
    wavelengths, Lw = split_spectrum(data_all, "Lw")
    wavelengths, R_rs = split_spectrum(data_all, "R_rs")

    return wavelengths, Ed, Lw, R_rs

def double_boxplot(data, label="", unit="", sensor_label="", band_labels=None, colours=None):
    if band_labels is None:
        band_labels = [""] * len(data)
    if colours is None:
        colours = ["k"] * len(data)

    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(10, data.shape[1]//3), tight_layout=True, sharey=True, gridspec_kw={"hspace": 0, "wspace": 0})
    bplot_main = axs[0].boxplot(data.T, vert=False, showfliers=False, whis=[5,95], patch_artist=True, labels=band_labels)
    for patch, colour in zip(bplot_main["boxes"], colours):
        patch.set_facecolor(colour)
    bplot_zoom = axs[1].boxplot(data.T, vert=False, showfliers=False, whis=[5,95], patch_artist=True, labels=band_labels)
    for patch, colour in zip(bplot_zoom["boxes"], colours):
        patch.set_facecolor(colour)

    for ax in axs:
        ax.set_xlabel(f"Difference [{unit}]")
        ax.grid(ls="--", color="0.5")

    axs[0].set_title("Tara Med.: "+sensor_label)

    xlim = axs[0].get_xlim()
    if xlim[0] > 0:
        axs[0].set_xlim(xmin=0)
    elif xlim[-1] < 0:
        axs[0].set_xlim(xmax=0)

    axs[1].tick_params(axis="y", left=False, labelleft=False)

    if label == "rel": # relative plot
        axs[1].set_xlim(-5.1, 5.1)
    else: # absolute plot
        axs[1].set_xlim(-30.1, 30.1)

    plt.savefig(f"results/Tara_med/{sensor_label}_{label}_double.pdf")
    plt.show()
    plt.close()

def make_boxplot(data, label="", unit="", sensor_label="", band_labels=None, colours=None):
    if band_labels is None:
        band_labels = [""] * len(data)
    if colours is None:
        colours = ["k"] * len(data)

    plt.figure(figsize=(5, data.shape[1]//3), tight_layout=True)
    bplot = plt.boxplot(data.T, vert=False, showfliers=False, whis=[5,95], patch_artist=True, labels=band_labels)
    for patch, colour in zip(bplot["boxes"], colours):
        patch.set_facecolor(colour)
    plt.xlabel(f"Difference [{unit}]")
    plt.title("Tara Med.: "+sensor_label)
    plt.grid(ls="--", color="0.5")

    xlim = plt.xlim()
    if xlim[0] > 0:
        plt.xlim(xmin=0)
    elif xlim[-1] < 0:
        plt.xlim(xmax=0)

    plt.tight_layout()
    plt.savefig(f"results/Tara_med/{sensor_label}_{label}.pdf")
    plt.show()
    plt.close()

def boxplot_relative(differences, band_labels=None, sensor_label="", **kwargs):
    if band_labels is None:
        band_labels = [""] * len(differences)

    medians, lower_error, upper_error = calculate_median_and_errors(differences)
    for band, med, low, up in zip(band_labels, medians, lower_error, upper_error):
        print(f"{sensor_label} {band} band: {med:+.2f} (+{up:.2f}, -{low:.2f}) %")

    make_boxplot(differences, label="rel", unit="%", sensor_label=sensor_label, band_labels=band_labels, **kwargs)
    double_boxplot(differences, label="rel", unit="%", sensor_label=sensor_label, band_labels=band_labels, **kwargs)

def boxplot_absolute(differences, band_labels=None, sensor_label="", scaling_exponent=6, **kwargs):
    if band_labels is None:
        band_labels = [""] * len(differences)

    differences_scaled = differences * 10**scaling_exponent
    unit = "$10^{-" + f"{scaling_exponent}" + "}$ sr$^{-1}$"

    medians, lower_error, upper_error = calculate_median_and_errors(differences_scaled)
    for band, med, low, up in zip(band_labels, medians, lower_error, upper_error):
        print(f"{sensor_label} {band} band: {med:+.2f} (+{up:.2f}, -{low:.2f}) x 10^-6 sr^-1")

    make_boxplot(differences_scaled, label="abs", unit=unit, sensor_label=sensor_label, band_labels=band_labels, **kwargs)
    double_boxplot(differences_scaled, label="abs", unit=unit, sensor_label=sensor_label, band_labels=band_labels, **kwargs)
