""" Command line parser """

import argparse
import os

script_name = 'flight_tracker'
description = """
Tool to monitor airline flights and optionally send notifications
when prices go below a set threshold/price point.\n
Track reward flights in Southwest Account (for the churners out there):
{0} -u <username> -p <password> [options]\n
Track cheapest flight (one way):
{0} -o <origin> -d <destination> -l <depart_date> [options]\n
Track cheapest flights (round trip):
{0} -o <origin> -d <destination> -l <depart_date>  -r <return_date> [options]
"""
description = description.format(script_name)
twilio_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'twilio.json'))


def parse_cl_arguments():
    parser = argparse.ArgumentParser(
        description=description,
        usage='{} [options]'.format(script_name),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.set_defaults(func=lambda x: parser.print_help())
    # General Arguments
    parser.add_argument('-f',
                        '--frequency',
                        metavar='',
                        type=float,
                        default=180,
                        help='Frequency (in minutes) for checking flights [%(default)s]')
    parser.add_argument('-la',
                        '--logall',
                        action='store_true',
                        help='Write/print all available flights')
    # SW Account
    swaccount = parser.add_argument_group('Southwest Account')
    swaccount.add_argument('-u',
                           '--username',
                           metavar='',
                           help='Southwest username')
    swaccount.add_argument('-p',
                           '--password',
                           metavar='',
                           help='Southwest password')
    swaccount.add_argument('-t',
                           '--threshold',
                           metavar='',
                           type=int,
                           default=1000,
                           help='Threshold (price difference) for notification [%(default)s]')
    # Flight Tracker
    track_flight = parser.add_argument_group('Track a Flight')
    track_flight.add_argument('-o',
                              '--origin',
                              metavar='',
                              help='Flight origin (airport code)')
    track_flight.add_argument('-d',
                              '--destination',
                              metavar='',
                              help='Flight destination (airport code)')
    track_flight.add_argument('-l',
                              '--depart_date',
                              type=str,
                              metavar='',
                              help='Depart date (mm/dd/yy)')
    track_flight.add_argument('-r',
                              '--return_date',
                              type=str,
                              metavar='',
                              help='Return date (mm/dd/yy)')
    track_flight.add_argument('-lt',
                              '--depart_time',
                              metavar='',
                              default='ALL_DAY',
                              choices=['ALL_DAY', 'BEFORE_NOON', 'NOON_TO_SIX', 'AFTER_SIX'],
                              help='Depart time {%(choices)s} [%(default)s]')
    track_flight.add_argument('-rt',
                              '--return_time',
                              metavar='',
                              default='ALL_DAY',
                              choices=['ALL_DAY', 'BEFORE_NOON', 'NOON_TO_SIX', 'AFTER_SIX'],
                              help='Return time {%(choices)s} [%(default)s]')
    track_flight.add_argument('-x',
                              '--passengers',
                              metavar='',
                              type=int,
                              default=1,
                              help='Number of passengers [%(default)s]')
    track_flight.add_argument('-ft',
                              '--faretype',
                              metavar='',
                              default='POINTS',
                              choices=['POINTS', 'USD'],
                              help='Fare type {%(choices)s} [%(default)s]')
    track_flight.add_argument('-c',
                              '--price_point',
                              type=float,
                              default=1,
                              metavar='',
                              help='Price point to receive notification [%(default)s]')
    track_flight.add_argument('-ns',
                              '--nonstop',
                              action='store_const',
                              const='True',
                              help='Only track non-stop flights')
    track_flight.add_argument('-n',
                              '--flight_numbers',
                              metavar='',
                              default=None,
                              nargs='+',
                              help=('Flight number (separate by spaces if separate flights,\n'
                                    'or commas if connecting flights)'))
    # Track multiple flights
    track_m_flights = parser.add_argument_group('Track Multiple Flights')
    track_m_flights.add_argument('-m',
                                 '--multiple',
                                 metavar='',
                                 help='File containing multiple flights to track (header must contain argument names)')
    # Notifications
    notifications = parser.add_argument_group('Notification Settings')
    notifications.add_argument('-a',
                               '--twilio',
                               metavar='',
                               type=str,
                               default=twilio_file,
                               help='Twilio account config file [%(default)s]')
    return parser.parse_args()
