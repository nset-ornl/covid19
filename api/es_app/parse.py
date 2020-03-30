from datetime import datetime
from hashlib import md5
from time import sleep
from typing import Dict, List, NoReturn, Union

import requests
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from es_app.common import get_var

Entry = Dict[str, Union[str, int, float]]
Doc = Dict[str, Union[str, int, float, Dict]]

ESUSER: str = get_var('ESUSER', '')
ESPASS: str = get_var('ESPASS', '')
ESHOSTS: str = get_var('ESHOSTS', '')
ESINDEX: str = get_var('ESINDEX', 'covid-ornl')
host_list: List[str] = ESHOSTS.split(',')
host_list: List[Dict] = [{'host': host} for host in host_list]

fips_skeleton: str = (
    "https://geo.fcc.gov/api/census/block/find"
    "?latitude={latitude}"
    "&longitude={longitude}"
    "&showall=false"
    "&format=json"
)


def get_elastic_client():
    tmp = Elasticsearch(
        hosts=host_list,
        http_auth=(ESUSER, ESPASS)
    )
    return tmp


class ElasticParse:
    _index = ESINDEX
    _type = 'record'

    def __init__(self, entries: List[Entry], op_type: str = 'index'):
        self.client = get_elastic_client()
        self._entries = entries
        if op_type not in ['index', 'create', 'update']:
            raise ValueError('Improper op_type given')
        self.op_type = op_type
        self.body_name = {
            'index': '_source',
            'create': '_source',
            'update': 'doc'
        }.get(self.op_type)

    @staticmethod
    def gen_id(entry: Entry) -> str:
        head = entry.get('county') or (entry.get('lat'), entry.get('lon'))
        if isinstance(head, tuple):
            head = ''.join(map(str, head))
        body = entry.get('state')
        tail = str(entry.get('scrape_group'))
        seed = ''.join((head, body, tail))
        return md5(seed.encode('utf-8')).hexdigest()

    @staticmethod
    def get_fips(lat: float, lon: float) -> Dict:
        fips_request = fips_skeleton.format(
            latitude=lat,
            longitude=lon
        )
        response = None
        attempts = 0
        while response is None:
            try:
                response = requests.get(fips_request)
            except requests.exceptions.RequestException:
                if attempts > 5:
                    raise
            else:
                if not 200 <= response.status_code < 300:
                    response = None
                else:
                    return response.json()
            sleep(pow(2, attempts))
            attempts += 1

    def entry_to_act(self, entry: Entry) -> Dict:
        doc: Doc = entry.copy()
        lat: None = None
        lon: None = None
        if 'lat' in doc:
            lat: float = doc.pop('lat')
        if 'lon' in doc:
            lon: float = doc.pop('lon')
        if lat is not None and lon is not None:
            doc['geometry'] = {
                'coordinates': [
                    lon,
                    lat
                ],
                'type': 'Point'
            }
            doc['fips'] = self.get_fips(lat=lat, lon=lon)
        doc['province/state'] = doc.pop('state', None)
        if isinstance(doc.get('updated'), str):
            doc['updated'] = datetime.strptime(
                doc['updated'],
                '%B %d, %Y'
            ).timestamp()
        if 'page' in doc:
            _ = doc.pop('page')
        doc['access_time'] = datetime.strptime(
            doc['access_time'],
            '%Y-%m-%d %H:%M:%S'
        ).timestamp()
        return {
            '_index': self._index,
            '_type': self._type,
            '_id': self.gen_id(entry),
            self.body_name: doc
        }

    def gen_actions(self) -> List[Dict]:
        actions = map(self.entry_to_act, self._entries)
        actions = list(actions)
        [act.update({'_op_type': self.op_type}) for act in actions]
        return actions

    def send_actions(self, actions: List[Dict] = None) -> NoReturn:
        if actions is None:
            actions = self.gen_actions()
        bulk(self.client, actions)
