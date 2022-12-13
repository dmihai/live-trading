# live-trading

Forex trading robot with configurable strategies.

## Setup

Make sure config.json and trading.json files are created and their content matcfhes the structure from config.json.sample and trading.json.sample

## Run

The script is designed to run only within forex trading session (Sun 9pm - Fri 2pm UTC). Trading ends Fri 2pm because we want to minimize the trades opened during weekend.

Only one instance of this script will run at one time. It is safe to run it using crontab:

    */10 * * * 0-5 /home/maverick/check-disk-space
