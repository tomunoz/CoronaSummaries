import pandas as pd
import numpy as numpy
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter, AutoMinorLocator)
import os

#
# the following files need to be in same directory as this file.
#       DifferenceTranspose.xlsx
#       DifferenceTransposeDeaths.xlsx
#       StatesDifferenceTranspose.xlsx
#       StatesDeathsDifferenceTranspose.xlsx
#
# these files are created by other 4 python scripts and need to run before this script.
#

# function to align x origin for 2 y axis
def align_yaxis(ax1, v1, ax2, v2):
    """adjust ax2 ylimit so that v2 in ax2 is aligned to v1 in ax1"""
    _, y1 = ax1.transData.transform((0, v1))
    _, y2 = ax2.transData.transform((0, v2))
    inv = ax2.transData.inverted()
    _, dy = inv.transform((0, 0)) - inv.transform((0, y1-y2))
    miny, maxy = ax2.get_ylim()
    ax2.set_ylim(miny+dy, maxy+dy)


def plot_data(data_df, is_US):
    #
    # define the plot object
    #
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    #
    # create the x tick marks (index) and the labels for the tick marks
    #
    x_labels = list(data_df.index.values)
    index = range(0, len(x_labels))
    #
    # associate the x tick marks with the x labels so the labels are not sorted alphabetically
    #
    i = 0
    label_interval = 6
    for i, item in enumerate(x_labels):
        if(i % label_interval != 0):
            x_labels[i] = ''
    plt.xticks(index, x_labels, rotation=90, fontsize='small')
    #
    # create a list of the deaths data to be graphed
    #
    infections_average = data_df["Infections 7 Day Average"].tolist()
    infections = data_df["Infections"].tolist()
    max_infections_average = max(infections_average)
    #
    deaths_average = data_df["Deaths 7 Day Average"].tolist()
    deaths = data_df["Deaths"].tolist()
    max_deaths_average = max(deaths_average)
    #
    # create the plot and display it
    #
    # plots to go on secondary y axis (right)
    deaths_average_curve = ax2.plot(index, deaths_average, label="Deaths Average", color='black', linestyle='dashed')
    deaths_curve = ax2.plot(index, deaths, label="Deaths", color='black')
    if ((max_infections_average - max_deaths_average) < 3000):
        correction_factor = 1
    elif ((max_infections_average - max_deaths_average) < 6000):
        correction_factor = 2
    elif ((max_infections_average - max_deaths_average) < 15000):
        correction_factor = 3
    else:
        correction_factor = 4
    upperlimit = max_deaths_average * ((max_infections_average - max_deaths_average)/max_deaths_average)/correction_factor
    ax2.set_ylim(0, upperlimit)
    # plots to go on primary y axis (left)
    infections_average_curve = ax1.plot(index, infections_average, label="Infections Average", color='g', linestyle='dashed')
    infections_curve = ax1.plot(index, infections, label="Infections", color='g')
    #
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Infections")
    ax1.yaxis.label.set_color('g')
    ax1.tick_params(axis='y', colors='g')
    ax1.tick_params(axis='x', labelrotation=90, labelsize=6)
    ax1.grid(True, axis='y', which='major', color='g', linestyle='-', linewidth=1.5)
    ax2.grid(True, axis='y', which='major', color='black', linestyle=':', linewidth=0.5)
    ax2.set_ylabel("Deaths")
    ax2.yaxis.label.set_color("black")
    #
    if (is_US == "Yes"):
        chart_title = state + " Infections & Deaths"
    else: 
        chart_title = nation + " Infections & Deaths"
    plt.title(chart_title)
    align_yaxis(ax1, 0, ax2, 0)
    plt.show()


def get_region(regions):
    print(regions)
    print('\n')
    while True:
        try:
            region = input("\nPlease enter a region (from list above): \n")
            print('\nRegion entered = ' + region + " \n")
        except ValueError:
            print("Sorry, please try again and check spelling. Pro tip: copy/paste from list above.")
            continue

        if region not in regions:
            print("Sorry, please enter a region name. Pro tip: copy/paste from list above.")
            continue
        else:
            break
    return region


os.system('clear')

#
# read files created from other scripts containing global data
#
global_infections_data_df = pd.read_excel("DifferenceTranspose.xlsx")
global_deaths_data_df = pd.read_excel("DifferenceTransposeDeaths.xlsx")
all_nations = list(global_deaths_data_df.columns)
nation = get_region(all_nations)

if nation == 'US':
    state_infections_data_df = pd.read_excel("StatesDifferenceTranspose.xlsx")
    state_deaths_data_df = pd.read_excel("StatesDeathsDifferenceTranspose.xlsx")
    states_territories = list(state_infections_data_df.columns)
    state = get_region(states_territories)

#
# create data frame to store data to be used for plotting
#
nation_data_df = pd.DataFrame()
nation_data_df["Infections"] = global_infections_data_df[nation]
nation_data_df["Deaths"] = global_deaths_data_df[nation]

#
# calculate 7-day averages for data and convent NaN to zero
#
nation_data_df["Infections 7 Day Average"] = nation_data_df.rolling(window=7)["Infections"].mean()
nation_data_df["Deaths 7 Day Average"] = nation_data_df.rolling(window=7)["Deaths"].mean()
nation_data_df = nation_data_df.fillna(0)

plot_data(nation_data_df, is_US="Not Necessarily")


#
# read state data only if nation == "US" up above.
# do not change the nation value here.
#

if nation == "US":
    state_data_df = pd.DataFrame()
    state_data_df["Infections"] = state_infections_data_df[state]
    state_data_df["Deaths"] = state_deaths_data_df[state]

    state_data_df["Infections 7 Day Average"] = state_data_df.rolling(window=7)["Infections"].mean()
    state_data_df["Deaths 7 Day Average"] = state_data_df.rolling(window=7)["Deaths"].mean()
    state_data_df = state_data_df.fillna(0)

    plot_data(state_data_df, is_US='Yes')
  



