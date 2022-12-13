# live-trading

Forex trading robot with configurable strategies.

## Setup

Make sure config.json and trading.json files are created and their content matches the structure from config.json.sample and trading.json.sample files.

## Run

The script is designed to run only within the forex trading session (Sun 9pm - Fri 2pm UTC). Trading ends Fri 2pm because we want to minimize the open trades during the weekend.

Only one instance of this script will run at one time. It is safe to run it using crontab:

    */10 * * * 0-5 cd /path/to/live-trading; python ./main.py
