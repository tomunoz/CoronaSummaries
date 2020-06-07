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
from datetime import datetime, timedelta

#
# functions to access web sites to scrape and confirm the web site is good
#
def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)

#
# since data is updated around 11:30pm easter, find yesterday's day after midnight to get latest update
#  and pdate url to scrape with yesterday's date
#
date_yesterday = datetime.strftime(datetime.now() - timedelta(1), '%m-%d-%Y')
url_date_yesterday = 'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_daily_reports/' + str(date_yesterday) + '.csv'

#
# scrape country, deaths, confirmed cases from CSEE Johns Hopkins University (JHU)
#
countries_unique = pd.DataFrame()
jhu_raw_html = simple_get(url_date_yesterday)
jhu_soup = BeautifulSoup(jhu_raw_html, 'lxml')
jhu_table = jhu_soup.find_all('table')[0]
jhu_df = pd.read_html(str(jhu_table))[0]
countries_unique['jhu'] = jhu_df['Country_Region'].unique()

#
# sum confirmed cases, deaths columns per country from JHU
#
country_records_sum = pd.DataFrame()
country_totals = pd.DataFrame()
for country in countries_unique['jhu']:
    country_records = jhu_df.loc[jhu_df['Country_Region'] == country, ['Country_Region', 'Confirmed', 'Deaths']]
    country_records_sum.at[0, 'Country'] = country
    country_records_sum.at[0, 'Confirmed'] = (country_records['Confirmed']).sum()
    country_records_sum.at[0, 'Deaths'] = (country_records['Deaths']).sum()
    country_records_sum.at[0, "Population"] = ''
    country_totals = country_totals.append(country_records_sum, ignore_index=True)

#
# scrape population by country data from World of Meters (WoM)
#
wom_pop_html = simple_get('https://www.worldometers.info/world-population/population-by-country')
wom_pop_countries_unique = pd.DataFrame()
wom_pop_soup = BeautifulSoup(wom_pop_html, 'lxml')
wom_pop_table = wom_pop_soup.find_all('table')[0]
wom_pop_df = pd.read_html(str(wom_pop_table))[0]
wom_pop_countries_unique['wom_pop'] = wom_pop_df['Country (or dependency)'].unique()
countries_unique = pd.concat([countries_unique, wom_pop_countries_unique], axis=1)
countries_unique.to_excel("CountriesUnique.xlsx")

#
# list of countries that are common to beoth JHU and WoM
#
common = list(set(countries_unique['jhu']) & set(countries_unique['wom_pop']))

#
# add countries from JHU to common that are not in WoM
#
common.append('US')
common.append('Taiwan*')
common.append('Cote d\'Ivoire')
common.append('Czechia')
common.append('Korea, South')
#common.append('Saint Kitts and Nevis')
common.append('Saint Vincent and the Grenadines')

#
# assign country names from WoM to JHU so can look up population from WoM
#
for country in common:
    new_country = ''
    if country == 'US':
        new_country = 'United States'
    elif country == 'Taiwan*':
        new_country = 'Taiwan'
    elif country == 'Cote d\'Ivoire':
        new_country = 'Côte d\'Ivoire'
    elif country == 'Czechia':
        new_country = 'Czech Republic (Czechia)'
    elif country == 'Korea, South':
        new_country = 'South Korea'
#    elif country == 'Saint Kitts and Nevis':
#        new_country == 'Saint Kitts & Nevis'
    elif country == 'Saint Vincent and the Grenadines':
        new_country = 'St. Vincent & Grenadines'
    else:
        new_country = country

#
# add 'Population' column to country_totals dataframe
#
    country_population = wom_pop_df.loc[wom_pop_df['Country (or dependency)'] == new_country, ['Country (or dependency)', 'Population (2020)']]
    this_population = country_population['Population (2020)']
    country_totals.loc[country_totals['Country'] == country, ['Population']] = int(this_population)

#
# remove countries for whom I couldn't get population data
#
country_totals['Population'].replace('', np.nan, inplace=True)
country_totals.dropna(subset=['Population'], inplace=True)

#
# calculate per capita data and multiply times 100 to make it a percent
#
country_totals['Confirmed/Population'] = (country_totals['Confirmed']/country_totals['Population']) * 100
country_totals['Deaths/Confirmed'] = (country_totals['Deaths'] /country_totals['Confirmed']) * 100
country_totals.sort_values(by=['Confirmed'], inplace=True, ascending=False)
country_totals.to_excel("CountryTotals.xlsx")

#
# variable to define minimum number of confirmed cases when pulling countries to display
#
case_limit = 2000

#
# create x, y bar chart for total confirmed cases per country
#
country_totals_list_confirmed = country_totals.loc[country_totals['Confirmed'] > case_limit]
country_totals_list_confirmed.sort_values(by=['Confirmed'], inplace=True, ascending=False)
country_totals_list_confirmed.to_excel("CountryTotalsList.xlsx", sheet_name='SortedConfirmed')
country_totals_list_confirmed.plot(kind='bar', x='Country', y='Confirmed')
plt.title('Confirmed Corona Virus Cases per Country (2000 Cases or More)')
plt.ylabel('# Confirmed Cases')
plt.grid(axis='y')

#
# create x, y bar chart for total deaths per country
#
country_totals_list_deaths = country_totals.loc[country_totals['Confirmed'] > case_limit]
country_totals_list_deaths.sort_values(by=['Deaths'], inplace=True, ascending=False)
country_totals_list_deaths.to_excel("CountryTotalsDeaths.xlsx", sheet_name='SortedDeaths')
country_totals_list_deaths.plot(kind='bar', x='Country', y='Deaths')
plt.title('Deaths Total per Country (for Countries with at least 2000 Confirmed Cases)')
plt.ylabel('# of Deaths')
plt.grid(axis='y')

#
# create x, y bar chart for % confirmed cases per capita by country
#
country_totals_list_confirmedpercent = country_totals.loc[country_totals['Confirmed'] > case_limit]
country_totals_list_confirmedpercent.sort_values(by=['Confirmed/Population'], inplace=True, ascending=False)
country_totals_list_confirmedpercent.to_excel("CountryTotalsListConfirmedPercent.xlsx", sheet_name='ConfirmedPercent')
country_totals_list_confirmedpercent.plot(kind='bar', x='Country', y='Confirmed/Population')
plt.title('Confirmed Corona Virus Cases as a Fraction of Country Population (for Countries with at least 2000 Confirmed Cases)')
plt.ylabel('(%) Confirmed Cases / Population')
plt.grid(axis='y')

#
# create x, y bar chart for % deaths as fraction of confirmed cases per country
#
country_totals_list_deathspercent = country_totals.loc[country_totals['Confirmed'] > case_limit]
country_totals_list_deathspercent.sort_values(by=['Deaths/Confirmed'], inplace=True, ascending=False)
country_totals_list_deathspercent.to_excel("CountryTotalsListDeathsPercent.xlsx", sheet_name='DeathsPercent')
country_totals_list_deathspercent.plot(kind='bar', x='Country', y='Deaths/Confirmed')
plt.title('Deaths from Corona Virus Cases as a Fraction of Confirmed Cases (for Countries with at least 2000 Confirmed Cases)')
plt.ylabel('(%) Deaths / Confirmed Cases')
plt.grid(axis='y')


#
# time series charts
#

#
# scrape country, deaths, confirmed cases from CSEE Johns Hopkins University (JHU)
#
countries_unique_ts_confirmed = pd.DataFrame()
jhu_ts_confirmed_raw_html = simple_get(
    'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
jhu_ts_confirmed_soup = BeautifulSoup(jhu_ts_confirmed_raw_html, 'lxml')
jhu_ts_confirmed_table = jhu_ts_confirmed_soup.find_all('table')[0]
jhu_ts_confirmed_df = pd.read_html(str(jhu_ts_confirmed_table))[0]
countries_unique_ts_confirmed['jhu'] = jhu_ts_confirmed_df['Country/Region'].unique()
jhu_ts_confirmed_df.to_excel("JHUTimeSeriesConfirmed.xlsx")

countries_unique_ts_deaths = pd.DataFrame()
jhu_ts_deaths_raw_html = simple_get(
    'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')
jhu_ts_deaths_soup = BeautifulSoup(jhu_ts_deaths_raw_html, 'lxml')
jhu_ts_deaths_table = jhu_ts_deaths_soup.find_all('table')[0]
jhu_ts_deaths_df = pd.read_html(str(jhu_ts_deaths_table))[0]
countries_unique_ts_deaths['jhu'] = jhu_ts_deaths_df['Country/Region'].unique()
jhu_ts_deaths_df.to_excel("JHUTimeSeriesDeaths.xlsx")

jhu_ts_confirmed_diff_df = jhu_ts_confirmed_df
jhu_ts_confirmed_diff_columns = list(jhu_ts_confirmed_diff_df.columns.values)
del jhu_ts_confirmed_diff_columns[0:5]




#
# sum confirmed cases, deaths columns per country from JHU
#
country_records_ts_confirmed_sum = pd.DataFrame()
country_totals_ts_confirmed = pd.DataFrame()
jhu_ts_confirmed_df_columns = list(jhu_ts_confirmed_df.columns.values)
del jhu_ts_confirmed_df_columns[0:5]
for country in countries_unique_ts_confirmed['jhu']:
    for column in jhu_ts_confirmed_df.columns[5:]:
        country_records_ts_confirmed = jhu_ts_confirmed_df.loc[jhu_ts_confirmed_df['Country/Region'] == country]
        country_records_ts_confirmed_sum.at[0, 'Country'] = str(country)
        country_records_ts_confirmed_sum.at[0, column] = country_records_ts_confirmed[column].sum()
    country_totals_ts_confirmed = country_totals_ts_confirmed.append(country_records_ts_confirmed_sum, ignore_index=True)
country_totals_ts_confirmed.to_excel("CountryTotalsTSConfirmed.xlsx")
country_records_ts_confirmed = jhu_ts_confirmed_df.loc[jhu_ts_confirmed_df['Country/Region'] == country]
country_totals_ts_confirmed.set_index('Country', inplace=True)
df_transpose = country_totals_ts_confirmed.transpose()
df_transpose.to_excel("Transposed.xlsx")


country_records_ts_deaths_sum = pd.DataFrame()
country_totals_ts_deaths = pd.DataFrame()
jhu_ts_deaths_df_columns = list(jhu_ts_deaths_df.columns.values)
del jhu_ts_deaths_df_columns[0:5]
for country in countries_unique_ts_deaths['jhu']:
    for column in jhu_ts_deaths_df.columns[5:]:
        country_records_ts_deaths = jhu_ts_deaths_df.loc[jhu_ts_deaths_df['Country/Region'] == country]
        country_records_ts_deaths_sum.at[0, 'Country'] = str(country)
        country_records_ts_deaths_sum.at[0, column] = country_records_ts_deaths[column].sum()
    country_totals_ts_deaths = country_totals_ts_deaths.append(country_records_ts_deaths_sum, ignore_index=True)
country_totals_ts_deaths.to_excel("CountryTotalsTSDeaths.xlsx")
country_records_ts_deaths = jhu_ts_deaths_df.loc[jhu_ts_deaths_df['Country/Region'] == country]
country_totals_ts_deaths.set_index('Country', inplace=True)
df_transpose_deaths = country_totals_ts_deaths.transpose()
df_transpose_deaths.to_excel("TransposedDeaths.xlsx")


x_ticks = range(0, len(df_transpose_deaths) + 10)
x_labels = df_transpose_deaths.index.values
line_labels = pd.DataFrame(columns=['Country', 'x', 'y'])
country_column = df_transpose_deaths.columns
line_labels_temp = pd.DataFrame()
for country in country_column:
    line_labels_temp.at[0, 'Country'] = country
    line_labels_temp.at[0, 'y'] = int(df_transpose_deaths[country].max())
    line_labels = line_labels.append(line_labels_temp, ignore_index=True)
line_labels['x'] = len(df_transpose_deaths)

'''
deaths_world_plot = df_transpose_deaths.plot(kind='line', x=df_transpose_deaths.index, y=df_transpose_deaths.columns, xticks=x_ticks, legend=False)
plt.xticks(rotation=90, fontsize='small')
plt.title('Confirmed Corona Virus Deaths Around the World')
plt.ylabel('# of Deaths')
deaths_world_plot.set_facecolor('#cceeff')
plt.grid(linestyle=':', linewidth='0.5', color='gray')
for key, row in line_labels.iterrows():
    country = row['Country']
    x = row['x']
    y = row['y']
    print(country + ' - ' + str(x) + ' - ' + str(y))
    plt.annotate(country, (x, y), ha='left', va='center', fontsize=8)
'''

df_transpose_min_deaths = pd.DataFrame()
for country in line_labels['Country']:
    df_transpose_deaths_temp = df_transpose_deaths.loc[df_transpose_deaths[country] > 0, [country]]
    if len(df_transpose_deaths_temp) > 0:
        df_transpose_deaths_temp.reset_index(inplace=True)
        print(df_transpose_deaths_temp)
        df_transpose_min_deaths = pd.concat([df_transpose_min_deaths, df_transpose_deaths_temp[country]], axis=1)
df_transpose_min_deaths.to_excel("MinDeaths.xlsx")

x_ticks = range(0, len(df_transpose_min_deaths) + 10)
x_labels = df_transpose_min_deaths.index.values
line_labels = pd.DataFrame(columns=['Country', 'x', 'y'])
country_column = df_transpose_min_deaths.columns
line_labels_temp = pd.DataFrame()
for country in country_column:
    line_labels_temp.at[0, 'Country'] = country
    line_labels_temp.at[0, 'y'] = int(df_transpose_min_deaths[country].max())
    line_labels = line_labels.append(line_labels_temp, ignore_index=True)
line_labels['x'] = len(df_transpose_min_deaths)

deaths_world_time_zero_plot = df_transpose_min_deaths.plot(kind='line', x=df_transpose_min_deaths.index, y=df_transpose_min_deaths.columns, xticks=x_ticks, legend=False)
plt.xticks(rotation=90, fontsize='small')
plt.title('Confirmed Corona Virus Deaths Around the World - Days Elapsed Since Time 0 (0 Deaths)')
plt.ylabel('# of Deaths Since Time Zero')
plt.xlabel('# of Days Elapsed')
deaths_world_time_zero_plot.set_facecolor('#cceeff')
plt.grid(linestyle=':', linewidth='0.5', color='gray')
for key, row in line_labels.iterrows():
    country = row['Country']
    x = row['x']
    y = row['y']
    print(country + ' - ' + str(x) + ' - ' + str(y))
    plt.annotate(country, (x, y), ha='left', va='center', fontsize=8)


#
# time series data line graphs for all countries (plan of record)
#
x_ticks = range(0, len(df_transpose) + 10)
x_labels = df_transpose.index.values
line_labels = pd.DataFrame(columns=['Country', 'x', 'y'])
country_column = df_transpose.columns
line_labels_temp = pd.DataFrame()
for country in country_column:
    line_labels_temp.at[0, 'Country'] = country
    line_labels_temp.at[0, 'y'] = int(df_transpose[country].max())
    line_labels = line_labels.append(line_labels_temp, ignore_index=True)
line_labels['x'] = len(df_transpose)
print(line_labels)

cases_world_plot = df_transpose.plot(kind='line', x=df_transpose.index, y=df_transpose.columns, xticks=x_ticks, legend=False)
plt.xticks(rotation=90, fontsize='small')
plt.title('Confirmed Corona Virus Cases Around the World')
plt.ylabel('# of Confirmed Cases')
cases_world_plot.set_facecolor('#cceeff')
plt.grid(linestyle=':', linewidth='0.5', color='gray')
for key, row in line_labels.iterrows():
    country = row['Country']
    x = row['x']
    y = row['y']
    print(country + ' - ' + str(x) + ' - ' + str(y))
    plt.annotate(country, (x, y), ha='left', va='center', fontsize=8)

#
# time series data line graphs based on time 0 alignment for all countries with minimal # of cases (days since cases = xxx)
#
df_transpose_min_cases = pd.DataFrame()
for country in line_labels['Country']:
    df_transpose_temp = df_transpose.loc[df_transpose[country] >= 1000, [
        country]]
    if len(df_transpose_temp) > 0:
        df_transpose_temp.reset_index(inplace=True)
        print(df_transpose_temp)
        df_transpose_min_cases = pd.concat([df_transpose_min_cases, df_transpose_temp[country]], axis=1)
df_transpose_min_cases.to_excel("MinCases.xlsx")

x_ticks = range(0, len(df_transpose_min_cases) + 10)
x_labels = df_transpose_min_cases.index.values
line_labels = pd.DataFrame(columns=['Country', 'x', 'y'])
country_column = df_transpose_min_cases.columns
line_labels_temp = pd.DataFrame()
for country in country_column:
    line_labels_temp.at[0, 'Country'] = country
    line_labels_temp.at[0, 'y'] = int(df_transpose_min_cases[country].max())
    line_labels = line_labels.append(line_labels_temp, ignore_index=True)
line_labels['x'] = len(df_transpose_min_cases)

line_labels.to_excel("LineLabels.xlsx")


cases_since_time_zero_plot = df_transpose_min_cases.plot(kind='line', x=df_transpose_min_cases.index, y=df_transpose_min_cases.columns, xticks=x_ticks, legend=False)
plt.xticks(rotation=90, fontsize='small')
plt.title('Confirmed Corona Virus Cases Around the World - Days Elapsed Since 1000 Cases')
plt.ylabel('# of Confirmed Cases')
plt.xlabel('# of Days Elapsed Since 1000 Cases')
cases_since_time_zero_plot.set_facecolor('#cceeff')
plt.grid(linestyle=':', linewidth='0.5', color='gray')
for key, row in line_labels.iterrows():
    country = row['Country']
    x = row['x']
    y = row['y']
    print(country + ' - ' + str(x) + ' - ' + str(y))
    plt.annotate(country, (x, y), ha='left', va='center', fontsize=8)


#
# Daily new confirmed cases
#
i = 1
diff_df_temp = pd.DataFrame()
total_columns = len(country_totals_ts_confirmed.columns)
print('Total columns = ' + str(total_columns))
thiscolname = country_totals_ts_confirmed.columns.values[total_columns - 1]
cases_threshold = country_totals_ts_confirmed.loc[country_totals_ts_confirmed[thiscolname] >= 10000]
print(cases_threshold)
for index in range(cases_threshold.shape[1] - 1):
   colname = cases_threshold.columns[index + i]
   prevcolname = cases_threshold.columns[index + i - 1]
   diff_df_temp[colname] = cases_threshold[colname] - cases_threshold[prevcolname]
   diff_df_temp.to_excel("Difference.xlsx")

diff_df = pd.DataFrame()
diff_df = diff_df_temp

diff_transpose_df = diff_df.transpose()
diff_transpose_df.to_excel("DifferenceTranspose.xlsx")

x_ticks = range(0, len(diff_transpose_df) + 10)
x_labels = diff_transpose_df.index.values
line_labels = pd.DataFrame(columns=['Country', 'x', 'y'])
country_column = diff_transpose_df.columns
line_labels_temp = pd.DataFrame()
for country in country_column:
    line_labels_temp.at[0, 'Country'] = country
    line_labels_temp.at[0, 'y'] = int(diff_transpose_df[country].iloc[-1])
    line_labels = line_labels.append(line_labels_temp, ignore_index=True)
line_labels['x'] = len(diff_transpose_df)

daily_new_cases_plot = diff_transpose_df.plot(kind='line', x=diff_transpose_df.index, y=diff_transpose_df.columns, xticks=x_ticks, legend=False, title="Daily New Cases")
plt.xticks(rotation=90, fontsize='small')
plt.title('Number of Daily New Confirmed Cases per Country (Countries with 10K or More Cases)')
plt.ylabel('# of Daily New Confirmed Cases')
plt.xlabel('Date')
#plt.ylim(0, 50000)
daily_new_cases_plot.set_facecolor('#cceeff')
plt.grid(linestyle=':', linewidth='0.5', color='gray')
#plt.legend()
for key, row in line_labels.iterrows():
    country = row['Country']
    x = row['x']
    y = row['y']
    plt.annotate(country, (x, y), ha='left', va='center', fontsize=6)



plt.show()

