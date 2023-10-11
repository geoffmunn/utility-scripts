#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import requests

from constants.constants import (
    CHAIN_DATA,
    CHECK_FOR_UPDATES,
    COIN_DIVISOR,
    COIN_DIVISOR_ETH,
    VERSION_URI
)
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins

def check_version():
    """
    Check the github repo to see if there's a new version.
    This check can be disabled by changing CHECK_FOR_UPDATES in the constants file.
    """

    if CHECK_FOR_UPDATES == True:
        local_json:json  = None
        remote_json:json = None

        print ('Checking for new version on Github...', end = '')
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

def coin_list(input: Coins, existingList: dict) -> dict:
    """ 
    Converts the Coins list into a dictionary.
    There might be a built-in function for this, but I couldn't get it working.
    """

    coin:Coin
    for coin in input:
        existingList[coin.denom] = coin.amount

    return existingList

def divide_raw_balance(amount:float, denom:str) -> float:
    """
    Return a human-readable amount depending on what type of coin this is.
    """

    result:float  = 0
    precision:int = getPrecision(denom)

    if precision == 6:
        result = float(amount) / COIN_DIVISOR
    else:
        result = float(amount) / COIN_DIVISOR_ETH

    return result

def getPrecision(denom:str) -> int:
    """
    Depending on the denomination, return the number of zeros that we need to account for

    Be default, it returns 6 digits
    """

    precision = 6

    if denom in CHAIN_DATA:
        precision = CHAIN_DATA[denom]['precision']

    return precision

def isDigit(value) -> bool:
    """
    A better method for identifying digits. This one can handle decimal places.
    """

    try:
        float(value)
        return True
    
    except ValueError:
        return False
    
def isPercentage(value:str) -> bool:
    """
    A helpter function to figure out if a value is a percentage or not.
    """
    last_char = str(value).strip(' ')[-1]
    if last_char == '%':
        return True
    
    else:
        return False
    
def multiply_raw_balance(amount:int, denom:str):
    """
    Return a human-readable amount depending on what type of coin this is.
    """
    result:float = 0

    if denom == 'weth-wei':
        result = float(amount) * COIN_DIVISOR_ETH
    else:
        result = float(amount) * COIN_DIVISOR

    return result
    
def strtobool(val):
    """
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Returns -1 if
    'val' is anything else.
    """

    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        #raise ValueError("invalid truth value %r" % (val,))
        return -1

def get_user_choice(question:str, allowed_options:list):
    """
    Get the user selection for a prompt and convert it to a standard value.
    This is typically a yes/no decision.
    """

    result = ''

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
