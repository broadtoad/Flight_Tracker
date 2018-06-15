from collections import defaultdict
import logging
import time
import sys

from .parse_cl_arguments import parse_cl_arguments
from .flight_records import create_flight_searches
from .utils import notify
from .web_scraper import find_cheapest_flights
from .web_scraper import find_all_destinations


logger = logging.getLogger()


def scrape_for_flights(flight_search):
    """ Scrape flights and return cheapest flights as TripRecord object """
    return find_cheapest_flights(flight_search)


def get_price_difference(cheapest_flights):
    """ Returns price_difference if price is below threshold/price point """
    if cheapest_flights:
        price_difference = cheapest_flights.price_difference
        if price_difference:
            return price_difference
        else:
            out_str = 'Cheapest itinerary is {} which is above price point'
            logger.info(out_str.format(cheapest_flights.price_str))
    else:
        logger.info('No flight options found matching itinerary')


def check_all_flights(args, flight_searches, price_notifications):
    """ Checks all flights in flight_searches and notifies if price has dropped """
    for idx, flight_search in enumerate(flight_searches):
        if idx > 0:
            wait_time = 3
            logger.info('Waiting {} seconds before checking next flight'.format(wait_time))
            time.sleep(wait_time)  # Wait a few seconds between queries
        cheapest_flights = scrape_for_flights(flight_search)
        price_difference = get_price_difference(cheapest_flights)
        if price_difference and price_difference not in price_notifications[flight_search]:
            out_str = cheapest_flights.output_string
            logger.info(out_str.replace('\n', ' '))
            notify(args, out_str)
            price_notifications[flight_search].add(price_difference)
        elif price_difference:
            logger.info('User already notified about this price change (ignoring)')


def main():
    # Set up logger
    fmt = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(filename='flights.log',
                        level=logging.INFO,
                        format=fmt)
    # Write to stdout as well
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(fmt))
    global logger
    logger.addHandler(console_handler)

    # Get arguments
    args = parse_cl_arguments()
    if len(sys.argv) == 1:  # Print help
        args.func(args)
        sys.exit()

    flight_searches = create_flight_searches(args)
    if args.flight_finder:
        find_all_destinations(flight_searches)
        sys.exit()

    price_notifications = defaultdict(set)
    while True:
        check_all_flights(args, flight_searches, price_notifications)
        if args.frequency == 0:
            logmsg = 'Frequency set to 0. Exiting'
            logger.info(logmsg)
            sys.exit()
        logger.info('Waiting {} minutes before checking again'.format(args.frequency))
        time.sleep(60 * args.frequency)


if __name__ == '__main__':
    main()
