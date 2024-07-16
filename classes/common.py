#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


import json
import os
import requests
import sqlite3
import traceback

from datetime import datetime, timedelta

from constants.constants import (
    CHAIN_DATA,
    CHECK_FOR_UPDATES,
    DB_FILE_NAME,
    VERSION_URI
)
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins

def check_version() -> bool:
    """
    Check the github repo to see if there's a new version.
    This check can be disabled by changing CHECK_FOR_UPDATES in the constants file.

    @params:
        - None

    @return: true/false if the script is on the current version
    """

    if CHECK_FOR_UPDATES == True:
        local_json:json  = None
        remote_json:json = None

        print ('\nChecking for new version on Github...')
        try:
            with open('version.json') as file:
                contents = file.read()
            
            local_json = json.loads(contents)
        except:
            print ('')
            print ('The local version.json file could not be opened.')
            print ('Please make sure you are using the latest version, check https://github.com/geoffmunn/utility-scripts for updates.')

        if local_json is not None:
            try:
                remote_json = requests.get(url = VERSION_URI, timeout = 1).json()
            except:
                print ('')
                print ('The remote version.json file could not be opened.')
                print ('Please make sure you are using the latest version, check https://github.com/geoffmunn/utility-scripts for updates.')
        else:
            return False
        
        if remote_json is not None:
            if local_json['version'] != remote_json['version']:
                print ('')

                local_bits = local_json['version'].split('.')
                remote_bits = remote_json['version'].split('.')

                if int(remote_bits[0]) > int(local_bits[0]):
                    print (' 🛎️  A new major version is available!')
                elif int(remote_bits[1]) > int(local_bits[1]):
                    print (' 🛎️  A new minor version is available!')
                elif int(remote_bits[2]) > int(local_bits[2]):
                    print (' 🛎️  An update is available!')
                elif int(local_bits[0]) > int(remote_bits[0]) or int(local_bits[1]) > int(remote_bits[1]) or int(local_bits[2]) > int(remote_bits[2]):
                    print (' 🛎️  You are running a version ahead of the official release!')
                    
                print (' 🛎️  Please check https://github.com/geoffmunn/utility-scripts for updates.')
                return False
            else:
                print ('... you have the latest version.')
                return True
        else:
            return False
    else:
        return True
    
def check_database() -> bool:
    """
    Check if the Osmosis database is present.

    @params:
        - None

    @return: true/false if the database is ok
    """

    try:
        if os.stat(DB_FILE_NAME).st_size > 0:
            # Check if the last scan was fairly recent:
            try:
                recent_scan = "SELECT last_scan_date FROM osmosis_summary WHERE ID = 1;"
                conn        = sqlite3.connect(DB_FILE_NAME)
                cursor      = conn.execute(recent_scan)

                for row in cursor.fetchone():
                    last_scan_date:datetime = datetime.strptime(row, '%Y-%m-%d %H:%M:%S')
                    previous_date:datetime  = datetime.now() - timedelta(weeks = 2)
                    
                    if last_scan_date < previous_date:
                        print ('\n 🗄  This database is out of date - you should get the latest Osmosis data.')
                        print (' 🗄  Run the get_osmosis_pools.py script to update the database.\n')

                conn.close()
            except:
                print (' 🛑 The Osmosis pool database could accessed...')
                print (' 🛑 Run \'get_osmosis_pools.py\' first to generate the list.\n')
                exit()

            # Make sure that the ibc_denoms table is there:
            ibc_table_exists:bool = True
            try:
                recent_scan = "SELECT * FROM ibc_denoms LIMIT 1;"
                conn        = sqlite3.connect(DB_FILE_NAME)
                cursor      = conn.execute(recent_scan)
                conn.close()
            except:
                ibc_table_exists = False

            if ibc_table_exists == False:
                print ('\n 🗄  No ibc_denom table found, creating one...')
                create_ibc_table = "CREATE TABLE ibc_denoms (ID INTEGER PRIMARY KEY AUTOINCREMENT, date_added DATETIME DEFAULT CURRENT_TIMESTAMP, ibc_denom TEXT NOT NULL, readable_denom TEXT NOT NULL);"
                conn   = sqlite3.connect(DB_FILE_NAME)
                cursor = conn.execute(create_ibc_table)
                conn.commit()
                conn.close()

            # Make sure that the ibc_denoms table is there:
            trading_table_exists:bool = True
            try:
                recent_scan = "SELECT * FROM trades LIMIT 1;"
                conn        = sqlite3.connect(DB_FILE_NAME)
                cursor      = conn.execute(recent_scan)
                conn.close()
            except:
                trading_table_exists = False

            if trading_table_exists == False:
                print ('\n 🗄  No trading table found, creating one...')
                create_trade_table = "CREATE TABLE trades (ID INTEGER PRIMARY KEY AUTOINCREMENT, date_added DATETIME DEFAULT CURRENT_TIMESTAMP, wallet_name TEXT NOT NULL, coin_from TEXT NOT NULL, amount_from INTEGER NOT NULL, price_from REAL NOT NULL, coin_to TEXT NOT NULL, amount_to INTEGER NOT NULL, price_to REAL NOT NULL, fees TEXT NOT NULL, exit_profit REAL NOT NULL, exit_loss REAL NOT NULL, linked_trade_id INTEGER, tx_hash TEXT NOT NULL, status TEXT NOT NULL);"
                conn               = sqlite3.connect(DB_FILE_NAME)
                cursor             = conn.execute(create_trade_table)
                conn.commit()
                conn.close()

            return True
        else:
            print (' 🛑 The Osmosis pool database is empty...')
            print (' 🛑 Run \'get_osmosis_pools.py\' first to generate the list.\n')
            exit()
    except OSError:
        print (' 🛑 The Osmosis pool database could not be found...')
        print (' 🛑 Run \'get_osmosis_pools.py\' first to generate the list.\n')
        exit()

def coin_list(input: Coins, existing_list: dict) -> dict:
    """
    Converts the Coins list into a dictionary.
    There might be a built-in function for this, but I couldn't get it working.

    @params:
        - input: a Coins collection
        - existing_list: a dictionary of coins we want to add the input coins to

    @return: a dictionary of coins
    """

    coin:Coin
    for coin in input:
        existing_list[coin.denom] = coin.amount

    return existing_list

def divide_raw_balance(amount:float, denom:str) -> float:
    """
    Return a human-readable amount depending on what type of coin this is.

    @params:
        - amount: the amount we want to convert
        - denom: the denom so we can figure out the precision

    @return: a human-readable amount of this denom
    """

    precision:int = get_precision(denom)
    result:float  = float(amount) / (10 ** precision)
    
    return result

def get_precision(denom:str) -> int:
    """
    Depending on the denomination, return the number of zeros that we need to account for

    Be default, it returns 6 digits

    @params:
        - denom: the denom so we can figure out the precision

    @return: the number of zeros that this denomination has
    """

    precision:int = 6

    if denom in CHAIN_DATA:
        precision = CHAIN_DATA[denom]['precision']

    return precision
    
def is_percentage(value:str) -> bool:
    """
    A helpter function to figure out if a value is a percentage or not.

    @params:
        - value: the value which needs to have a '%' character at the end

    @return: true/false this value is a percentage
    """

    last_char = str(value).strip(' ')[-1]
    if last_char == '%':
        return True
    
    else:
        return False
    
def multiply_raw_balance(amount:int, denom:str) -> float:
    """
    Return a human-readable amount depending on what type of coin this is.

    @params:
        - amount: the amount we want to convert
        - denom: the denom so we can figure out the precision

    @return: a human-readable amount of this denom
    """

    precision:int = get_precision(denom)
    result:float  = float(amount) * (10 ** precision)

    return result

def strtobool(val:str) -> bool:
    """
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Returns -1 if
    'val' is anything else.

    @params:
        - val: the amount we want to check

    @return: true/false this value is a boolean
    """

    # Just in case we have been passed a boolean, convert it to a string
    val = str(val)
    
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        #raise ValueError("invalid truth value %r" % (val,))
        return -1

def get_user_choice(question:str, allowed_options:list) -> str:
    """
    Get the user selection for a prompt and convert it to a standard value.
    This is typically a yes/no decision.

    @params:
        - question: what question are we prompting the user with?
        - allowed_options: the available answers for the user

    @return: the answer the user provides
    """

    result:str = ''

    while True:    
        answer = input(question).lower()
        
        if len(allowed_options) == 0:
            result = strtobool(answer)
            
            if result != -1:
                break
        else:
            if answer in allowed_options:
                result = answer
                break

    return result

