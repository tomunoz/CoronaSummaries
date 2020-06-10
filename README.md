# CoronaSummaries
Personal python scripts that scrape covid-19 data from Johns Hopkins github repo (https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data)

Johns Hopkins data is updated around 11:30pm Eastern so these scripts should be run after midnight.

5 python scripts:

GlobalCoronaDailyInfections.py
  Creates various charts of infections, cumulative and daily, at global level for countries that exceed a minimum threshold of infections.

GlobalCoronaDailyDeaths.py
  Creates various charts of national deaths, cumulative and daily, at global level for countries

USCoronaDailyInfections.py
  Same as GlobalCoronaDailyInfections.py but for US states only

USCoronaDailyDeaths.py
  Same as GlobalCoronaDailyDeaths.py but for US states only

NationTrend.py
  Creates a country view of infections and deaths plus running 7 day average for each.
  Needs to be run after the other 4 scripts are finished since they create 4 xlsx files used by this script
       DifferenceTranspose.xlsx
       DifferenceTransposeDeaths.xlsx
       StatesDifferenceTranspose.xlsx
       StatesDeathsDifferenceTranspose.xlsx


There are some enhancements I'd like to make as time allows:
1] Create a web up to display these visuals
2] Allow selections at the country level and the US state level in web app so it's not a bunch of graphs on glass
3] Log scale views
4] Running average views
