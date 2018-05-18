""" Classes to help manage flight queries and flight results """

from datetime import datetime
from collections import OrderedDict
import logging
import sys


logger = logging.getLogger(__name__)


class FlightSearch(object):
    def __init__(self, origin, destination, depart_date, depart_time='ALL_DAY',
                 return_date=None, return_time=None, passengers=1,
                 senior_passengers=0, faretype='POINTS', passenger_type='ADULT',
                 promo_code=None, price_point=0, flight_numbers=None, logall=False,
                 nonstop=False):
        self.origin = origin
        self.destination = destination
        self.depart_date = depart_date
        self.depart_time = depart_time
        self.return_date = return_date
        self.return_time = return_time
        self.num_passengers = int(passengers)
        self.senior_passengers = senior_passengers
        self.faretype = faretype
        self.passenger_type = passenger_type
        self.promo_code = promo_code
        self.price_point = int(price_point)
        self.flight_numbers = flight_numbers
        self.logall = logall
        self.nonstop = nonstop

    @property
    def return_destination(self):
        return self.origin if self.return_date else None

    @property
    def return_time_str(self):
        return 'ALL_DAY' if (self.return_date and not self.return_time) else self.return_time

    @property
    def triptype(self):
        return 'roundtrip' if self.return_date else 'oneway'

    @staticmethod
    def convert_to_datetime(text, fmt_date=False):
        accepted_formats = ['%Y-%m-%d', '%m/%d/%y', '%m/%d/%Y', '%m/%d/%y %A']
        for fmt in accepted_formats:
            try:
                date = datetime.strptime(text, fmt)
                if fmt_date:
                    return date.strftime('%Y-%m-%d')
                else:
                    return date
            except (ValueError, TypeError):
                pass

    @property
    def depart_date_str(self):
        date = self.convert_to_datetime(self.depart_date, True)
        if type(date) == str:
            return date
        else:
            sys.exit('Date format does not match expected format mm/dd/yy')

    @property
    def return_date_str(self):
        return self.convert_to_datetime(self.return_date, True)

    @property
    def return_date_dt(self):
        return self.convert_to_datetime(self.return_date)

    @property
    def depart_date_dt(self):
        return self.convert_to_datetime(self.depart_date)

    @property
    def flight_search_dict(self):
        sw_keys = ['originationAirportCode', 'destinationAirportCode', 'returnAirportCode',
                   'departureDate', 'departureTimeOfDay', 'returnDate', 'returnTimeOfDay',
                   'adultPassengersCount', 'seniorPassengersCount', 'fareType', 'passengerType',
                   'tripType', 'promoCode', 'reset', 'redirectToVision', 'int',
                   'leapfrogRequest', 'application', 'site']
        sw_values = [self.origin, self.destination, self.return_destination,
                     self.depart_date_str, self.depart_time,
                     self.return_date_str, self.return_time_str,
                     self.num_passengers, self.senior_passengers, self.faretype, self.passenger_type,
                     self.triptype, self.promo_code, 'true', 'true', 'HOMEQBOMAIR',
                     'true', 'air-booking', 'southwest']
        sw_values = [x if x is not None else '' for x in sw_values]
        sw_dict = OrderedDict(zip(sw_keys, sw_values))
        return sw_dict

    def __str__(self):
        outstr = ('Flight on {} from {} to {} (triptype={}, faretype={}, '
                  'price_point={})')
        return outstr.format(self.depart_date, self.origin, self.destination,
                             self.triptype, self.faretype, self.price_point)

    def __repr__(self):
        class_name = self.__class__.__name__
        output = []
        for k, v in self.__dict__.items():
            if type(v) is str:
                fmt = '{}="{}"'.format(k, v)
            elif k == 'search_instance':
                fmt = '{}={}'.format(k, str(v.__repr__()))
            else:
                fmt = '{}={}'.format(k, v)
            output.append(fmt)
        return '{}({})'.format(class_name, ', '.join(output))


class FlightRecord(FlightSearch):
    def __init__(self, origin, destination, depart_date, depart_time, arrival_time,
                 flight_numbers, price, fare_class, search_instance):
        self.origin = origin
        self.destination = destination
        self.depart_date = depart_date
        self.depart_time = depart_time
        self.arrival_time = arrival_time
        self.flight_numbers = flight_numbers
        self.search_instance = search_instance
        self.price = price * self.search_instance.num_passengers
        self.fare_class = fare_class

    @property
    def triptype(self):
        return self.search_instance.triptype

    @property
    def faretype(self):
        return self.search_instance.faretype

    @property
    def price_point(self):
        return self.search_instance.price_point

    @property
    def price_str(self):
        if self.faretype == 'USD':
            return '$' + '{0:.2f}'.format(self.price)
        else:
            return str(int(self.price)) + ' points'

    @property
    def output_list(self):
        return [self.origin, self.destination, self.depart_date, self.depart_time,
                self.arrival_time, str(self.flight_numbers), self.price_str,
                self.fare_class]


class TripRecord(object):
    def __init__(self, flights):
        self.flights = flights
        self.search_instance = flights[0].search_instance
        self.price_point = self.search_instance.price_point
        self.faretype = self.search_instance.faretype
        self.price = sum([flight.price for flight in self.flights])

    def __iter__(self):
        for flight in self.flights:
            yield flight

    def __repr__(self):
        return 'TripRecord({})'.format(self.flights)

    def _convert_price_to_str(self, price):
        if self.faretype == 'USD':
            return '$' + '{0:.2f}'.format(price)
        else:
            return str(int(price)) + ' points'

    @property
    def price_difference(self):
        price_flights = self.price
        price_point = self.price_point
        if price_flights < price_point:
            return self._convert_price_to_str(price_point - price_flights)

    @property
    def price_str(self):
        return self._convert_price_to_str(self.price)

    @property
    def output_string(self):
        flight_info = self.flights[0]
        origin = flight_info.origin
        destination = flight_info.destination
        date = flight_info.depart_date_dt.strftime('%m/%d/%y')
        flight_numbers = flight_info.flight_numbers
        depart_time = flight_info.depart_time
        arrival_time = flight_info.arrival_time
        out_str = ('Alert: Flights from {} to {} on {} have gone down in price. '
                   'Current price is {} which is {} below threshold.\n\nFlight Numbers: {}\n'
                   'Departure: {}\nArrival: {}')
        price_str = self.price_str
        price_difference = self.price_difference
        out_str = out_str.format(origin, destination, date, price_str,
                                 price_difference, flight_numbers, depart_time,
                                 arrival_time)
        return out_str


def create_flight_search_from_args(args):
    """ Creates FlightSearch object from args """
    if not (args.origin and args.destination and args.depart_date):
        sys.exit('Origin, destination and depart date are required for flight tracking')
    # Fix flight numbers
    if args.flight_numbers:
        if not isinstance(args.flight_numbers, list):
            if ' ' in args.flight_numbers:
                args.flight_numbers = args.flight_numbers.split(' ')
            else:
                args.flight_numbers = [args.flight_numbers]
        args.flight_numbers = [list(map(int, x.split(','))) for x in args.flight_numbers]
    flight_args = args.__dict__.copy()
    remove_args = ['twilio', 'frequency', 'multiple', 'func']
    for e_arg in remove_args:
        del flight_args[e_arg]
    return FlightSearch(**flight_args)


def create_flight_searches_from_file(args):
    """ Creates list of FlightSearch objects from file """
    flight_file = open(args.multiple, 'r')
    data = [x.strip().split('\t') for x in flight_file.readlines()]
    header = data[0]
    flight_searches = []

    for entry in data[1:]:
        if len(header) != len(entry):
            sys.exit('All fields in file must be filled in (use true/false when applicable)')
        for argname, argval in zip(header, entry):
            if 'false' in argval.lower():
                args.__setattr__(argname, None)
            else:
                args.__setattr__(argname, argval)

        flight_searches.append(create_flight_search_from_args(args))
    logger.info('Collected {} flights to track from file'.format(len(flight_searches)))
    return flight_searches


def create_flight_searches(args):
    if args.multiple:
        flight_searches = create_flight_searches_from_file(args)
    else:
        flight_searches = [create_flight_search_from_args(args)]
    return flight_searches
