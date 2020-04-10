#!/usr/bin/env python3

import requests
import datetime
import json
import os
from numpy import nan
import pandas as pd
from cvpy.static import ColumnHeaders as Headers


country = 'US'
state = 'New York'
provider = 'state'
url = 'https://health.data.ny.gov/resource/xdss-u53e.json'


columns = Headers.updated_site
row_csv = []

raw_data = requests.get(url).json()
access_time = datetime.datetime.utcnow()
resolution = 'county'

with open('new_york_state_data.json', 'w') as f:
    json.dump(raw_data, f)

def fill_in_df(df_list, dict_info, columns):
    if isinstance(df_list, list):
        all_df = []
        for each_df in df_list:
            each_df['provider'] = dict_info['provider']
            each_df['country'] = dict_info['country']
            each_df['state'] = dict_info['state']
            each_df['resolution'] = dict_info['resolution']
            each_df['url'] = dict_info['url']
            each_df['page'] = str(dict_info['page'])
            each_df['access_time'] = dict_info['access_time']
            df_columns = list(each_df.columns)
            for column in columns:
                if column not in df_columns:
                    each_df[column] = nan
                else:
                    pass
            all_df.append(each_df.reindex(columns=columns))
        final_df = pd.concat(all_df)
    else:
        df_list['provider'] = dict_info['provider']
        df_list['country'] = dict_info['country']
        df_list['state'] = dict_info['state']
        df_list['resolution'] = dict_info['resolution']
        df_list['url'] = dict_info['url']
        df_list['page'] = str(dict_info['page'])
        df_list['access_time'] = dict_info['access_time']
        df_columns = list(df_list.columns)
        for column in columns:
            if column not in df_columns:
                df_list[column] = nan
            else:
                pass
        final_df = df_list.reindex(columns=columns)
    return final_df


df = pd.DataFrame(raw_data).sort_values('test_date', ascending=False)
df['test_date'] = pd.to_datetime(df['test_date'])
df['test_date'] = df['test_date'].dt.strftime('%Y-%m-%d')
day_before = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime(
    '%Y-%m-%d')
df[df['test_date'] == day_before].sort_values('county').drop(
    ['new_positives', 'total_number_of_tests', 'test_date'], axis = 1)

df = df[df['test_date'] == day_before].sort_values('county').drop(
    ['new_positives', 'total_number_of_tests', 'test_date'], axis = 1)
df.columns = ['county', 'cases', 'tested']

dict_info_county = {'provider': 'state', 'country': country, "url": url,
                   "state": state, "resolution": "county",
                   "page": str(raw_data), "access_time": access_time}

df = fill_in_df(df, dict_info_county, columns)

now = datetime.datetime.now()
dt_string = now.strftime("_%Y-%m-%d_%H%M")
path = os.getenv("OUTPUT_DIR", "")
file_name = path + state.replace(' ', '_') + dt_string + '.csv'

# df = pd.DataFrame(row_csv, columns=columns)
# all_df = pd.concat([df, county_level_df])
df.to_csv(file_name, index=False)
