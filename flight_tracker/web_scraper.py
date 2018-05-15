""" Module to help with web scraping """

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

from collections import OrderedDict
from collections import defaultdict
import logging
import time
import re

from .flight_records import (
    FlightSearch,
    FlightRecord,
    TripRecord
)
from .utils import create_table


logger = logging.getLogger(__name__)


def create_driver():
    """ Create chrome driver instance """
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('--no-sandbox')
    my_driver = webdriver.Chrome(chrome_options=options)
    return my_driver


def wait_for(name, obj_type='class_name', timeout=7):
    """ Websites take time - this function checks if website loaded properly """
    obj_type = obj_type.lower()
    try:
        if obj_type == 'class_name':
            element_present = ec.presence_of_element_located((By.CLASS_NAME, name))
        elif obj_type == 'xpath':
            element_present = ec.presence_of_element_located((By.XPATH, name))
        elif obj_type == 'id':
            element_present = ec.presence_of_element_located((By.ID, name))
        elif obj_type == 'name':
            element_present = ec.presence_of_element_located((By.NAME, name))
        else:
            raise Exception('Object type {} not found'.format(obj_type))
        WebDriverWait(driver, timeout).until(element_present)
        return element_present
    except TimeoutException:
        logger.error('Timed out waiting for page to load')
        logger.error(driver.current_url)


def elements_to_list(elements):
    """ Convert selenium elements list to list of strings """
    return list(map(lambda x: str(x.text), elements))


def go_to_url(url, wait_obj, obj_type='class_name'):
    """ Creates driver if not present and loads url """
    if 'driver' not in globals():
        global driver
        driver = create_driver()
    driver.get(url)
    return wait_for(wait_obj, obj_type)


def get_sw_point_purchases():
    """ Collects user flights purchased with points """
    logger.info('Fetching user flight purchases')
    account_url = 'https://www.southwest.com/myaccount/rapid-rewards/recent-activity/details'
    result_obj, result_type = ('secondary-page--table-row', 'class_name')
    go_to_url(account_url, wait_obj=result_obj, obj_type=result_type)
    time.sleep(2)
    data = driver.find_elements_by_class_name(result_obj)

    points_dict = defaultdict(lambda: 0)
    for row in data:
        desc = row.find_element_by_class_name('recent-activity-details--table-description').text
        if 'REDEEM' in desc:
            confirmation = str(desc.split()[2])
            points_info = row.find_element_by_class_name('swa-g-screen-reader-only').text
            points = int(points_info.split()[-2].replace(',', ''))
            if points < points_dict[confirmation]:
                points_dict[confirmation] = points
    return points_dict


def get_sw_user_flight_info(trip_url, args, points_dict):
    """ Function to create FlightSearch object from a user trip URL """
    result_obj, result_type = ('flight-details--flight-number', 'class_name')
    go_to_url(trip_url, result_obj, result_type)
    time.sleep(2)

    trips = driver.find_elements_by_class_name('flight-details--header')
    conf_num = str(driver.find_element_by_class_name('upcoming-details--confirmation-number').text)
    price = points_dict.get(conf_num)
    # Update price with threshold
    price -= args.threshold

    dates = elements_to_list(driver.find_elements_by_class_name('flight-details--travel-date'))
    if len(trips) == 2:
        depart_date, return_date = dates
    else:
        depart_date = dates[0]  # have not tested one-way with SW user
        return_date = None

    trip_infos = driver.find_elements_by_class_name('flight-details--columns')
    cities = elements_to_list(trip_infos[0].find_elements_by_class_name('flight-details--city'))

    flight_numbers = [elements_to_list(trip_info.find_elements_by_class_name('flight-details--flight-number'))
                      for trip_info in trip_infos]
    flight_numbers = [list(map(int, flight_num)) for flight_num in flight_numbers]
    origin, destination = cities[0], cities[-1]

    logger.info('Fetched user flight information for flight from {} to {}'.format(origin, destination))
    return FlightSearch(origin, destination, depart_date,
                        return_date=return_date, flight_numbers=flight_numbers,
                        price_point=price, logall=args.logall)


def check_sw_account(args):
    """ Checks user account and returns FlightSearch objects for
    all itineraries. """
    # Log in to Southwest
    login_url = 'https://www.southwest.com/flight/login'
    result_obj, result_type = ('credential', 'name')
    go_to_url(login_url, result_obj, result_type)

    logger.info('Logging into Southwest account...')
    username = driver.find_element_by_name('credential')
    password = driver.find_element_by_name('password')
    username.clear()
    username.send_keys(args.username)
    password.clear()
    password.send_keys(args.password)
    driver.find_element_by_name('submit').click()
    if not wait_for('trip-details-content'):
        logger.info('Could not log in... check Southwest credentials')
        return

    # Get flights associated with account
    trips = driver.find_elements_by_class_name('trip-details-content')
    trip_urls = [trip.find_element_by_css_selector('a').get_attribute('href') for trip in trips]
    points_dict = get_sw_point_purchases()
    my_trips = []
    for trip_url in trip_urls:
        my_trips.append(get_sw_user_flight_info(trip_url, args, points_dict))
    logger.info('Found {} trips in account'.format(len(my_trips)))
    return my_trips


def get_all_available_sw_flights(args):
    """ Function to collect all available flights using FlightSearch
    objects. All available flights from a FlightSearch object are returned.
    """
    # Search for flight
    logstr = 'Collecting all available flights from {} to {} on {}'
    logger.info(logstr.format(args.origin, args.destination, args.depart_date_str))

    result_table_xpath = './/*[contains(@id, "air-booking-product")]'
    result_row_xpath = './/*[contains(@class, "air-booking-select-detail")]'
    result_type = 'xpath'
    result = go_to_url(args.southwest_url, result_table_xpath, result_type)
    if not result:
        logger.info('No flights found')
        return

    # Extract flight details
    flight_options = []
    all_flights = driver.find_elements_by_xpath(result_table_xpath)[0:2]  # Max 2: RT
    for i, route in enumerate(all_flights):
        if i == 0:
            origin, destination = args.origin, args.destination
            depart_date = args.depart_date
        else:
            origin, destination = args.destination, args.origin
            depart_date = args.return_date
        route_flights = route.find_elements_by_xpath(result_row_xpath)
        for flight in route_flights:
            prices = elements_to_list(flight.find_elements_by_class_name('fare-button--value-total'))
            times = elements_to_list(flight.find_elements_by_class_name('time--value'))
            flight_nums = elements_to_list(flight.find_elements_by_class_name('actionable--text'))[0]
            flight_nums = list(map(int, re.findall('(\d+)', flight_nums)))
            if not prices:
                continue  # skip if sold out
            prices = [int(str(price).replace(',', '').replace('$', '')) for price in prices]
            price = min(prices)
            depart_time, arrive_time = times
            flight_option = FlightRecord(origin, destination, depart_date,
                                         depart_time, arrive_time, flight_nums,
                                         price, args)
            flight_options.append(flight_option)
    logger.info('Found {} flights'.format(len(flight_options)))

    if args.logall:
        header = ['Origin', 'Destination', 'Date', 'DepartTime', 'ArriveTime',
                  'FlightNums', 'Price']
        data = [x.output_list for x in flight_options]
        table = create_table(header, data)
        logstr = 'Printing results table:\n\n{}\n'.format(table)
        logger.info(logstr)
    return flight_options


def find_cheapest_flights(flight_search):
    """ From one-way or round trip flight_search, return a TripRecord object
    containing the cheapest flight(s)
    """
    flight_results = []
    flights = get_all_available_sw_flights(flight_search)
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


if __name__ == '__main__':
    driver = create_driver()
