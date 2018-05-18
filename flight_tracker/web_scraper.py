""" Module to help with web scraping """

from collections import OrderedDict
from datetime import datetime
import logging
import re
import requests
import json


from .flight_records import (
    FlightSearch,
    FlightRecord,
    TripRecord
)
from .utils import create_table

# Suppress insecure requests (issue with MacOS/Python3.6)
try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass

logger = logging.getLogger(__name__)


class SWApi(object):
    """ API wrapper for querying flights """
    def __init__(self):
        self._session = requests.Session()
        self.base_url = 'https://www.southwest.com/'
        self.flights_api = 'api/air-booking/v1/air-booking/page/air/booking/shopping'

    def post(self, url, **kwargs):
        success_codes = [200, 400]
        response = self._session.post(url, verify=False, **kwargs)
        status_code = response.status_code
        if status_code not in success_codes:
            print(response.text)
            err = 'Invalid status code received. Expected {}. Received {}.'
            raise Exception(err.format(success_codes, status_code))
        else:
            return response.text

    def _get_url(self, api):
        return self.base_url + api

    def _get_headers(self, mobile_api=False):
        api_key = 'l7xx944d175ea25f4b9c903a583ea82a1c4c'
        api_key = mobile_api if mobile_api else api_key
        return {'x-api-key': api_key,
                'content-type': 'application/json',
                'token': self.access_token if hasattr(self, 'access_token') else None
                }

    def retrieve_raw_flight_data(self, search_data):
        flight_api_url = self._get_url(self.flights_api)
        return self.post(flight_api_url, data=json.dumps(search_data), headers=self._get_headers())


def convert_to_datetime(date, fmt='%Y-%m-%dT%H:%M:%S',
                        return_date=False, return_time=False):
    date_datetime = datetime.strptime(date, fmt)
    if return_date and return_time:
        return date_datetime.strftime('%m/%d/%y'), date_datetime.strftime('%I:%M %p')
    elif return_date:
        return date_datetime.strftime('%m/%d/%y')
    elif return_time:
        return date_datetime.strftime('%I:%M %p')
    else:
        return date_datetime


def retrieve_flight_data(args, sw_api):
    """ Use SW_API to return list of FlightRecord objects """
    logstr = 'Collecting all available flights from {} to {} on {}'
    logger.info(logstr.format(args.origin, args.destination, args.depart_date_str))
    search_data = args.flight_search_dict
    raw_data = sw_api.retrieve_raw_flight_data(search_data)
    data = json.loads(raw_data)
    flight_results = data['data']['searchResults']['airProducts']
    flight_options = []
    for flight_route in flight_results:
        route_results = flight_route['details']
        for flight in route_results:
            fares_dict = flight['fareProducts']['ADULT']
            fare_info = get_minimum_fare(fares_dict)
            if fare_info:
                fare_class, price, currency_type = fare_info
                price = float(price)
                origin = flight['originationAirportCode']
                destination = flight['destinationAirportCode']
                flight_numbers = list(map(int, flight['flightNumbers']))
                depart_datetime = flight['departureDateTime'].split('.')[0]
                arrival_datetime = flight['arrivalDateTime'].split('.')[0]
                depart_date, depart_time = convert_to_datetime(depart_datetime, return_date=True, return_time=True)
                arrival_date, arrival_time = convert_to_datetime(arrival_datetime, return_date=True, return_time=True)
                flight_option = FlightRecord(origin, destination, depart_date,
                                             depart_time, arrival_time, flight_numbers,
                                             price, fare_class, args)
                flight_options.append(flight_option)
    logger.info('Found {} flights'.format(len(flight_options)))
    if args.logall:
        header = ['Origin', 'Destination', 'Date', 'DepartTime', 'ArriveTime',
                  'FlightNums', 'Price', 'FareClass']
        data = [x.output_list for x in flight_options]
        table = create_table(header, data)
        logstr = 'Printing results table:\n\n{}\n'.format(table)
        logger.info(logstr)
    return flight_options


def get_minimum_fare(all_fares):
    """ From fare dict, return a list containing the type, price,
    and currency type from the minimum price in dict """
    fares = []  # type, price, currency_type
    for fare_type, fare_dict in all_fares.items():
        fare_available = fare_dict['fare']
        if fare_available:
            fare_info = fare_dict['fare']['totalFare']
            fare_price = fare_info['value']
            currency_type = fare_info['currencyCode']
            fares.append([fare_type, fare_price, currency_type])
    if fares:
        return min((fare for fare in fares), key=lambda x: x[1])


def find_cheapest_flights(flight_search):
    """ From one-way or round trip flight_search, return a TripRecord object
    containing the cheapest flight(s)
    """
    sw_api = SWApi()
    flight_results = []
    flights = retrieve_flight_data(flight_search, sw_api)
    if not flights:
        return
    if flight_search.flight_numbers:
        for flight in flights:
            if flight.flight_numbers in flight_search.flight_numbers:
                flight_results.append(flight)
    else:
        # Get min for each origin
        flights_dict = OrderedDict()
        for flight in flights:
            if flight_search.nonstop:
                if len(flight.flight_numbers) > 1:  # skip connecting flights if nonstop
                    continue
            if flight.origin not in flights_dict:
                flights_dict[flight.origin] = flight
            else:
                if flights_dict[flight.origin].price > flight.price:
                    flights_dict[flight.origin] = flight
        flight_results = list(flights_dict.values())
    if flight_results:
        if flight_search.triptype == 'roundtrip':
            if len(flight_results) != 2:
                return None
        return TripRecord(flight_results)
