""" Utils for flight_tracker"""

from twilio.rest import Client
import json
import logging

logger = logging.getLogger(__name__)


def create_table(header, data):
    output = [header] + data
    tab_length = 4
    lengths = [max(len(str(x)) for x in line) + tab_length for line in zip(*output)]
    row_formatter = ''.join(['{:' + str(x) + 's}' for x in lengths])
    output_str = '\n'.join([row_formatter.format(*row) for row in output])
    return output_str


def notify(args, price_alert):
    """ Send notification via Twilio if notification hasn't already been sent """
    # Change twilio logging 
    twilio_logger = logging.getLogger('twilio.http_client')
    twilio_logger.setLevel(logging.WARNING)
    if args.twilio in ('None', 'False'):
        return
    twilio_dict = {str(k): str(v) for k, v in json.load(open(args.twilio)).items()}
    if twilio_dict['account'] == 'twilio_account':
        logger.info('Please update twilio.json file for notifications.')
    else:
        client = Client(twilio_dict['account'], twilio_dict['auth_token'])
        client.api.account.messages.create(
            to=twilio_dict['to'],
            from_=twilio_dict['from'],
            body=price_alert)
        logger.info('User notified.')
