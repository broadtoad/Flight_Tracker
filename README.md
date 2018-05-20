# Flight_Tracker
Tool to monitor airline flights (SW) and optionally send notifications when prices go below a set threshold/price point.

Tool can be used to monitor cheapest roundtrip or oneway flights, or specific flights using the `--flight_numbers` flag.

Notes: Use at your own risk. Scraping data may be in violation of flight company's Terms of Service.
Flight tracking by user account has been removed. SW changes their website too often for this to work
long term.


## Installation
1. Clone/download repository:<br>
`git clone https://github.com/broadtoad/Flight_Tracker.git`
2. Sign up for an account with [Twilio](https://www.twilio.com/) and edit `twilio.json` to receive notifications
3. Install application<br>
`cd Flight_Tracker` `python setup.py install`

For flight tracking, I recommend running the script on [Amazon Web Services](https://aws.amazon.com/free/) (it's free, and you can protect yourself from incurring fees by using a Visa gift card).

Tested on AWS Linux, MacOS, Python2.7, Python3.6


## Usage
Command line arguments:
<pre>
usage: flight_tracker [options]

Tool to monitor airline flights and optionally send notifications
when prices go below a set threshold/price point.

Track cheapest flight (one way):
flight_tracker -o origin -d destination -l depart_date [options]

Track cheapest flights (round trip):
flight_tracker -o origin -d destination -l depart_date -r return_date [options]

Track multiple flights:
flight_tracker -m multiple_flights.txt

optional arguments:
  -h, --help            show this help message and exit
  -f , --frequency      Frequency (in minutes) for checking flights [180]
  -la, --logall         Write/print all available flights

Track a Flight:
  -o , --origin         Flight origin (airport code)
  -d , --destination    Flight destination (airport code)
  -l , --depart_date    Depart date (mm/dd/yy)
  -r , --return_date    Return date (mm/dd/yy)
  -lt , --depart_time   Depart time {ALL_DAY, BEFORE_NOON, NOON_TO_SIX, AFTER_SIX} [ALL_DAY]
  -rt , --return_time   Return time {ALL_DAY, BEFORE_NOON, NOON_TO_SIX, AFTER_SIX} [ALL_DAY]
  -x , --passengers     Number of passengers [1]
  -ft , --faretype      Fare type {POINTS, USD} [POINTS]
  -p , --price_point    Price point to receive notification [1]
  -ns, --nonstop        Only track non-stop flights
  -c, --companion       Companion booking (set passengers = 2, report price for 1)
  -n  [ ...], --flight_numbers  [ ...]
                        Flight number (separate by spaces if separate flights,
                        or commas if connecting flights)

Track Multiple Flights:
  -m , --multiple       File containing multiple flights to track (header must contain argument names)

Notification Settings:
  -a , --twilio         Twilio account config file [twilio.json]
</pre>

## Examples
Track a single flight:
<pre>
# Track oneway flight and notify if less than $150
flight_tracker -o PHL -d BNA -l 07/12/18 -p 150 -ft USD

# Track oneway flight (nonstop only) and notify if less than $150
flight_tracker -o PHL -d BNA -l 07/12/18 -p 150 -ft USD -ns

# List all roundtrip flight options
flight_tracker -o PHL -d BNA -l 07/12/18 -r 07/20/18 -la -f 0

# Track roundtrip flight and notify if less than 20000 points
flight_tracker -o PHL -d BNA -l 07/12/18 -r 07/20/18 -p 20000

# Track specific rountrip flight and notify if less than $400
flight_tracker -o PHL -d BNA -l 07/12/18 -r 07/20/18 -p 400 -n 2506,2568 874 -ft USD
</pre>
Track multiple flights:

`multiple_flights.txt`:


| origin | destination | depart_date | return_date | flight_numbers | nonstop | faretype | price_point |
|--------|-------------|-------------|-------------|----------------|---------|----------|-------------|
| PHL    | BNA         | 7/12/18     | FALSE       | FALSE          | FALSE   | USD      | 150         |
| PHL    | BNA         | 7/12/18     | FALSE       | FALSE          | TRUE    | USD      | 150         |
| PHL    | BNA         | 7/12/18     | 7/20/18     | FALSE          | FALSE   | POINTS   | 20000       |
| PHL    | BNA         | 7/12/18     | 7/20/18     | 2506,2568 874  | FALSE   | USD      | 400         |

<pre>
flight_tracker -m multiple_flights.txt
</pre>
Note: You can opt out of notifications by setting `--twilio None` or leaving `twilio.json` as is.

## Inspirations
[swa-dashboard](https://github.com/gilby125/swa-dashboard)

[SWA-Scraper](https://github.com/wcrasta/SWA-Scraper) @wcrasta
