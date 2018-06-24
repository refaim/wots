import http.client
import logging
import urllib.parse
from datetime import datetime
from decimal import Decimal
from typing import *

import requests


class TcgPlayerHttpException(Exception):
    def __init__(self, response: requests.Response):
        super().__init__({ 'code': response.status_code, 'head': response.headers, 'body': response.text })
        self.response: requests.Response = response

class TcgPlayerCategory(object):
    def __init__(self):
        self.id: int = None
        self.name: str = None
        self.name_display: str = None
        self.name_seo: str = None
        self.label: str = None
        self.label_sealed: str = None
        self.condition_guide_url: str = None
        self.is_scannable: bool = None
        self.popularity: int = None
        self.modified_at: datetime = None

class TcgPlayerGroup(object):
    def __init__(self):
        self.id: int = None
        self.name: str = None
        self.abbreviation: Optional[str] = None
        self.supplemental: bool = None
        self.published_at: datetime = None
        self.modified_at: datetime = None

class TcgPlayerProduct(object):
    def __init__(self):
        self.id: int = None
        self.category_id: int = None
        self.group_id: int = None
        self.name: str = None
        self.url: str = None
        self.image_url: str = None
        self.modified_at: datetime = None

class TcgPlayerProductPrice(object):
    def __init__(self):
        self.id: int = None
        self.price_low: Decimal = None
        self.price_low_direct: Decimal = None
        self.price_mid: Decimal = None
        self.price_high: Decimal = None
        self.price_market: Decimal = None
        self.is_foil: bool = None

class TcgPlayerCommunicator(object):
    DATE_FORMAT = '%m/%d/%Y'
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

    MTG_CATEGORY_ID = 1

    def __init__(self, secret_key: str, public_key: str, token: Optional[str]) -> None:
        self.secret_key = secret_key
        self.public_key = public_key
        self.token = token
        self.logger = logging.getLogger()

    def __raw_request(self, method: str, path: str, payload: dict, headers: dict) -> dict:
        params_key = { 'GET': 'params', 'POST': 'data' }[method]
        kwargs = { params_key: payload, 'headers': {**headers, **{ 'Accept': 'application/json' }}, 'allow_redirects': False }
        self.logger.info('[BEGIN] %s %s', method, path)
        response = requests.request(method, urllib.parse.urljoin('https://api.tcgplayer.com', path), **kwargs)
        self.logger.info('[READY] %d %s %s %s', response.status_code, http.client.responses[response.status_code], method, path)
        try:
            json = response.json()
        except ValueError:
            json = None
        failed = response.status_code != requests.codes.ok
        failed = failed or json is None or not json.get('success', True) or len(json.get('errors', [])) > 0
        if failed:
            raise TcgPlayerHttpException(response)
        return json.get('results', json)

    def __request(self, method: str, path: str, payload: dict) -> Optional[dict]:
        attempts = len(['login', 'request'])
        while attempts > 0:
            attempts -= 1
            try:
                if self.token is None:
                    self.__login()
                return self.__raw_request(method, path, payload, { 'Authorization': 'Bearer {}'.format(self.token) })
            except TcgPlayerHttpException as e:
                if e.response.status_code == requests.codes.unauthorized:
                    self.token = None
                    continue
                raise
        return None

    def __request_paginated(self, path: str, payload: dict) -> Iterable[dict]:
        step = 20
        offset = 0
        complete = False
        while not complete:
            try:
                response = self.__request('GET', path, {**payload, **{ 'limit': step, 'offset': offset }})
                for item in response:
                    yield item
                complete = response == []
            except TcgPlayerHttpException as e:
                if e.response.status_code == requests.codes.not_found:
                    json = e.response.json()
                    if not json.get('success', True) and len(json.get('results', [])) == 0:
                        complete = True
                        continue
                raise
            offset += step

    def __login(self) -> None:
        data = self.__raw_request('POST', '/token', { 'grant_type': 'client_credentials', 'client_id': self.public_key, 'client_secret': self.secret_key }, {})
        self.token = data['access_token']

    def get_token(self) -> Optional[str]:
        return self.token

    def __parse_datetime(self, value: str) -> datetime:
        if '.' not in value:
            value = '{}.00'.format(value)
        return datetime.strptime(value, self.DATETIME_FORMAT)

    def list_categories(self) -> Iterable[TcgPlayerCategory]:
        for entry in self.__request_paginated('/catalog/categories', {}):
            model = TcgPlayerCategory()
            model.id = entry['categoryId']
            model.name = entry['name']
            model.name_display = entry['displayName']
            model.name_seo = entry['seoCategoryName']
            model.label = entry['nonSealedLabel']
            model.label_sealed = entry['sealedLabel']
            model.condition_guide_url = entry['conditionGuideUrl']
            model.is_scannable = entry['isScannable']
            model.popularity = entry['popularity']
            model.modified_at = self.__parse_datetime(entry['modifiedOn'])
            yield model

    def list_groups(self, category_id: int) -> Iterable[TcgPlayerGroup]:
        for entry in self.__request_paginated('/catalog/categories/{}/groups'.format(category_id), {}):
            model = TcgPlayerGroup()
            model.id = entry['groupId']
            model.name = entry['name']
            model.abbreviation = entry['abbreviation']
            model.supplemental = entry['supplemental']
            model.published_at = datetime.strptime(entry['publishedOn'], self.DATE_FORMAT)
            model.modified_at = self.__parse_datetime(entry['modifiedOn'])
            yield model

    def list_cards(self, category_id: int, group_id: int) -> Iterable[TcgPlayerProduct]:
        for entry in self.__request_paginated('/catalog/products', { 'categoryId': category_id, 'groupId': group_id, 'productTypes': 'Cards' }):
            model = TcgPlayerProduct()
            model.id = entry['productId']
            model.category_id = entry['categoryId']
            model.group_id = entry['groupId']
            model.name = entry['productName']
            model.url = entry['url']
            model.image_url = entry['image']
            model.modified_at = self.__parse_datetime(entry['modifiedOn'])
            yield model

    def list_prices(self, group_id: int) -> Iterable[TcgPlayerProductPrice]:
        for entry in self.__request('GET', '/pricing/group/{}'.format(group_id), {}):
            model = TcgPlayerProductPrice()
            model.id = entry['productId']
            model.price_low = entry['lowPrice']
            model.price_mid = entry['midPrice']
            model.price_high = entry['highPrice']
            model.price_market = entry['marketPrice']
            model.price_low_direct = entry['directLowPrice']
            subType = entry['subTypeName']
            if subType not in ['Normal', 'Foil']:
                self.logger.warning('Unknown subtype %s', subType)
            model.is_foil = subType == 'Foil'
            yield model
