#!/usr/bin/env python3

import requests
import datetime
from numpy import nan
import pandas as pd
from cvpy.static import Headers


country = 'US'
date_url = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y%m%d')
url = 'http://www.dph.illinois.gov/sites/default/files/COVID19/COVID19CountyResults'+date_url+'.json'
state = 'Illinois'
resolution = 'county'
columns = Headers.updated_site

raw_data = requests.get(url).json()
access_time = datetime.datetime.utcnow()
row_csv = []

updated_date = raw_data['LastUpdateDate']
for feature in raw_data['characteristics_by_county']['values']:
    county_name = feature['County']
    # This gives the whole state total
    if county_name == 'Illinois':
        resolution = 'state'
        county = nan
    else:
        resolution = 'county'
        county = county_name

    cases = feature['confirmed_cases']
    tested = feature['total_tested']
    negative_tests = feature['negative']
    deaths = feature['deaths']

    row_csv.append([
        'state', country, state, nan,
        url, str(raw_data), access_time, county,
        cases, nan, deaths, nan,
        nan, tested, nan, negative_tests,
        nan, nan, nan, nan, nan,
        nan, nan, nan,
        nan, nan, nan,
        nan, nan, nan,
        resolution, nan, nan, nan,
        nan, nan, nan, nan,
        nan, nan, nan, nan,
        nan, nan, nan,
        nan, nan,
        nan, nan, nan, nan,
        nan, nan])




df = pd.DataFrame(row_csv, columns=columns)
df.to_csv('illinois_.csv', index=False)
