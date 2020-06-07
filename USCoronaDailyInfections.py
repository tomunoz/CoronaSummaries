from requests import get
import requests
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import itertools
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta



#
# time series charts
#

###################################################################################################

#
# US time series data confirmed
#

#us_states_ts_confirmed_df = pd.read_excel("Covid19USConfirmedTimeSeries.xlsx")

us_states_ts_confirmed_df = pd.read_csv("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv", error_bad_lines=False)


us_states_unique_ts_confirmed = pd.DataFrame()
us_states_unique_ts_confirmed['state'] = us_states_ts_confirmed_df['Province_State'].unique()
us_states_ts_confirmed_df.to_excel("Covid19USTimeSeriesOut.xlsx")

temp_frame = pd.DataFrame()
temp_frame = us_states_ts_confirmed_df.drop(
    ['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Province_State', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'], axis=1)

#for (column, data) in temp_frame.iteritems():
#    new_date = pd.to_datetime(column, format='%Y-%m-%d %H:%M:%S').strftime("%m/%d")
#    us_states_ts_confirmed_df.rename(columns={column: new_date}, inplace=True)

for (column, data) in temp_frame.iteritems():
    new_date = pd.to_datetime(column, format='%m/%d/%y').strftime("%m/%d")
    us_states_ts_confirmed_df.rename(columns={column: new_date}, inplace=True)

us_states_ts_confirmed_df.to_excel("Covid19USTimeSeriesOutnewdate.xlsx")


#
# sum confirmed cases, deaths columns per state from JHU
#
us_states_records_ts_confirmed_sum = pd.DataFrame()
us_states_totals_ts_confirmed = pd.DataFrame()
us_states_ts_confirmed_df_columns = list(us_states_ts_confirmed_df.columns.values)
del us_states_ts_confirmed_df_columns[0:5]
for state in us_states_unique_ts_confirmed['state']:
    for column in us_states_ts_confirmed_df.columns[6:]:
        us_states_records_ts_confirmed = us_states_ts_confirmed_df.loc[us_states_ts_confirmed_df['Province_State'] == state]
        us_states_records_ts_confirmed_sum.at[0, 'state'] = str(state)
        us_states_records_ts_confirmed_sum.at[0, column] = us_states_records_ts_confirmed[column].sum()
    us_states_totals_ts_confirmed = us_states_totals_ts_confirmed.append(us_states_records_ts_confirmed_sum, ignore_index=True)
us_states_totals_ts_confirmed.to_excel("stateTotalsTSConfirmed.xlsx")
us_states_records_ts_confirmed = us_states_ts_confirmed_df.loc[us_states_ts_confirmed_df['Province_State'] == state]
us_states_totals_ts_confirmed = us_states_totals_ts_confirmed.drop(
    ['Province_State', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'], axis=1)
us_states_totals_ts_confirmed.set_index('state', inplace=True)
df_transpose_us = us_states_totals_ts_confirmed.transpose()
df_transpose_us.to_excel("StatesTransposed.xlsx")
print(df_transpose_us.keys())


#
# time series data line graphs for all countries (plan of record)
#
x_ticks = range(0, len(df_transpose_us) + 10)
x_labels = df_transpose_us.index.values
print(x_labels)
line_labels = pd.DataFrame(columns=['state', 'x', 'y'])
state_column = df_transpose_us.columns
line_labels_temp = pd.DataFrame()
for state in state_column:
    line_labels_temp.at[0, 'state'] = state
    line_labels_temp.at[0, 'y'] = int(df_transpose_us[state].max())
    line_labels = line_labels.append(line_labels_temp, ignore_index=True)
line_labels['x'] = len(df_transpose_us)

us_total_cases_plot = df_transpose_us.plot(kind='line', x=df_transpose_us.index, y=df_transpose_us.columns, xticks=x_ticks, legend=False)
plt.xticks(rotation=90, fontsize='small')
plt.title('Confirmed Cases in the US')
plt.ylabel('# of Confirmed Cases')
us_total_cases_plot.set_facecolor('#ffe6ff')
plt.grid(linestyle=':', linewidth='0.5', color='gray')
for key, row in line_labels.iterrows():
    state = row['state']
    x = row['x']
    y = row['y']
    print(state + ' x = ' + str(x) + ' y = ' + str(y))
    plt.annotate(state, (x, y), ha='left', va='center', fontsize=8)

#
# time series data line graphs based on time 0 alignment for all countries with minimal # of cases (days since cases = xxx)
#
df_transpose_us_min_cases = pd.DataFrame()
for state in line_labels['state']:
    df_transpose_us_temp = df_transpose_us.loc[df_transpose_us[state] > 0, [state]]
    if len(df_transpose_us_temp) > 0:
        df_transpose_us_temp.reset_index(inplace=True)
        df_transpose_us_min_cases = pd.concat([df_transpose_us_min_cases, df_transpose_us_temp[state]], axis=1)
df_transpose_us_min_cases.to_excel("StatesMinCases.xlsx")

x_ticks = range(0, len(df_transpose_us_min_cases) + 10)
x_labels = df_transpose_us_min_cases.index.values
line_labels = pd.DataFrame(columns=['state', 'x', 'y'])
state_column = df_transpose_us_min_cases.columns
line_labels_temp = pd.DataFrame()
for state in state_column:
    line_labels_temp.at[0, 'state'] = state
    line_labels_temp.at[0, 'y'] = int(df_transpose_us_min_cases[state].max())
    line_labels = line_labels.append(line_labels_temp, ignore_index=True)
line_labels['x'] = len(df_transpose_us_min_cases)

us_daily_new_cases_plot = df_transpose_us_min_cases.plot(
    kind='line', x=df_transpose_us_min_cases.index, y=df_transpose_us_min_cases.columns, xticks=x_ticks, legend=False)
plt.xticks(rotation=90, fontsize='small')
plt.title('Confirmed Cases in the US - Days Elapsed Since 1 Case')
plt.ylabel('# of Confirmed Cases')
plt.xlabel('# of Days Elapsed Since 1st Case')
us_daily_new_cases_plot.set_facecolor('#ffe6ff')
plt.grid(linestyle=':', linewidth='0.5', color='gray')
for key, row in line_labels.iterrows():
    state = row['state']
    x = row['x']
    y = row['y']
    plt.annotate(state, (x, y), ha='left', va='center', fontsize=8)


#
# Daily new confirmed cases
#
i = 1
diff_df_temp = pd.DataFrame()
total_columns = len(us_states_totals_ts_confirmed.columns)
thiscolname = us_states_totals_ts_confirmed.columns.values[total_columns - 1]
cases_threshold = us_states_totals_ts_confirmed.loc[us_states_totals_ts_confirmed[thiscolname] >= 0]
for index in range(cases_threshold.shape[1] - 1):
   colname = cases_threshold.columns[index + i]
   prevcolname = cases_threshold.columns[index + i - 1]
   diff_df_temp[colname] = cases_threshold[colname] - cases_threshold[prevcolname]
   diff_df_temp.to_excel("StatesDifference.xlsx")

diff_df = pd.DataFrame()
diff_df = diff_df_temp

diff_transpose_df = diff_df.transpose()
diff_transpose_df.to_excel("StatesDifferenceTranspose.xlsx")

x_ticks = range(0, len(diff_transpose_df) + 10)
x_labels = diff_transpose_df.index.values
line_labels = pd.DataFrame(columns=['state', 'x', 'y'])
state_column = diff_transpose_df.columns
line_labels_temp = pd.DataFrame()
for state in state_column:
    line_labels_temp.at[0, 'state'] = state
    line_labels_temp.at[0, 'y'] = int(diff_transpose_df[state].iloc[-1])
    line_labels = line_labels.append(line_labels_temp, ignore_index=True)
line_labels['x'] = len(diff_transpose_df)

us_daily_cases_plot = diff_transpose_df.plot(kind='line', x=diff_transpose_df.index, y=diff_transpose_df.columns, xticks=x_ticks, legend=False, title="Daily New Cases")
plt.xticks(rotation=90, fontsize='small')
plt.title('Number of Daily New Confirmed Cases per state')
plt.ylabel('# of Daily New Confirmed Cases')
plt.xlabel('Date')
us_daily_cases_plot.set_facecolor('#ffe6ff')
#plt.ylim(0, 40000)
plt.grid(linestyle=':', linewidth='0.5', color='gray')
for key, row in line_labels.iterrows():
    state = row['state']
    x = row['x']
    y = row['y']
    plt.annotate(state, (x, y), ha='left', va='center', fontsize=6)



plt.show()

