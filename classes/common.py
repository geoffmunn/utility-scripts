#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import requests

#from classes.wallet import UserWallet

from constants.constants import (
    CHAIN_DATA,
    CHECK_FOR_UPDATES,
    COIN_DIVISOR,
    COIN_DIVISOR_ETH,
    FULL_COIN_LOOKUP,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
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
    
# def get_coin_selection(question:str, coins:dict, only_active_coins:bool = True, estimation_against:dict = None, wallet:UserWallet = False):
#     """
#     Return a selected coin based on the provided list.
#     """

#     label_widths = []

#     label_widths.append(len('Number'))
#     label_widths.append(len('Coin'))
#     label_widths.append(len('Balance'))

#     if estimation_against is not None:
#         label_widths.append(len('Estimation'))
#         swaps_tx = wallet.swap().create()

#     wallet:UserWallet = UserWallet()
#     coin_list     = []
#     coin_values   = {}

#     coin_list.append('')

#     for coin in FULL_COIN_LOOKUP:

#         if coin in coins:
#             coin_list.append(coin)
#         elif only_active_coins == False:
#             coin_list.append(coin)

#         coin_name = FULL_COIN_LOOKUP[coin]
#         if len(str(coin_name)) > label_widths[1]:
#             label_widths[1] = len(str(coin_name))

#         if coin in coins or only_active_coins == False:

#             if coin in coins:
#                 coin_val = wallet.formatUluna(coins[coin], coin)

#                 if len(str(coin_val)) > label_widths[2]:
#                     label_widths[2] = len(str(coin_val))

#             if estimation_against is not None:

#                 # Set up the swap details
#                 swaps_tx.swap_amount        = float(wallet.formatUluna(estimation_against['amount'], estimation_against['denom'], False))
#                 swaps_tx.swap_denom         = estimation_against['denom']
#                 swaps_tx.swap_request_denom = coin

#                 # Change the contract depending on what we're doing
#                 swaps_tx.setContract()
                
#                 if coin != estimation_against['denom']:
#                     estimated_value:float = swaps_tx.swapRate()

#                 else:
#                     estimated_value:str   = None
                
#                 coin_values[coin] = estimated_value
                
#                 if len(str(estimated_value)) > label_widths[3]:
#                     label_widths[3] = len(str(estimated_value))

#     padding_str   = ' ' * 100
#     header_string = ' Number |'

#     if label_widths[1] > len('Coin'):
#         header_string += ' Coin' + padding_str[0:label_widths[1] - len('Coin')] + ' |'
#     else:
#         header_string += ' Coin |'

#     if label_widths[2] > len('Balance'):
#         header_string += ' Balance ' + padding_str[0:label_widths[2] - len('Balance')] + '|'
#     else:
#         header_string += ' Balance |'

#     if estimation_against is not None:
#         if label_widths[3] > len('Estimation'):
#             header_string += ' Estimation ' + padding_str[0:label_widths[3] - len('Estimation')] + '|'
#         else:
#             header_string += ' Estimation |'

#     horizontal_spacer = '-' * len(header_string)

#     coin_to_use:str           = None
#     returned_estimation:float = None    
#     answer:str                = False
#     coin_index:dict           = {}

#     while True:

#         count:int = 0

#         print ('\n' + horizontal_spacer)
#         print (header_string)
#         print (horizontal_spacer)

#         for coin in FULL_COIN_LOOKUP:

#             if coin in coins or estimation_against is not None:
#                 count += 1
#                 coin_index[FULL_COIN_LOOKUP[coin].lower()] = count
            
#             if coin_to_use == coin:
#                 glyph = '✅'
#             elif estimation_against is not None and estimation_against['denom'] == coin:
#                 glyph = '⚪'
#             else:
#                 glyph = '  '

#             count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
           
#             coin_name = FULL_COIN_LOOKUP[coin]
#             if label_widths[1] > len(coin_name):
#                 coin_name_str = coin_name + padding_str[0:label_widths[1] - len(coin_name)]
#             else:
#                 coin_name_str = coin_name

#             if coin in coins:
#                 coin_val = wallet.formatUluna(coins[coin], coin)

#                 if label_widths[2] > len(str(coin_val)):
#                     balance_str = coin_val + padding_str[0:label_widths[2] - len(coin_val)]
#                 else:
#                     balance_str = coin_val
#             else:
#                 coin_val    = ''
#                 balance_str = coin_val + padding_str[0:label_widths[2] - len(coin_val)]

#             if coin in coins or only_active_coins == False:
#                 if estimation_against is None:
#                     print (f"{count_str}{glyph} | {coin_name_str} | {balance_str}")
#                 else:
#                     if coin in coin_values:
#                         if coin_values[coin] is not None:
#                             estimated_str:str = str(("%.6f" % (coin_values[coin])).rstrip('0').rstrip('.'))
#                         else:
#                             estimated_str = '--'
#                     else:
#                         estimated_str = ''

#                     print (f"{count_str}{glyph} | {coin_name_str} | {balance_str} | {estimated_str}")
    
#         print (horizontal_spacer + '\n')

#         answer = input(question).lower()
        
#         # Check if a coin name was provided:
#         if answer in coin_index:
#             answer = str(coin_index[answer])

#         if answer.isdigit() and int(answer) > 0 and int(answer) <= count:
#             if estimation_against is not None and estimation_against['denom'] == coin_list[int(answer)]:
#                 print ('\nYou can\'t swap to the same coin!')
#             else:
            
#                 returned_estimation:float = None
#                 coin_to_use:str           = coin_list[int(answer)] 

#                 if estimation_against is not None:
#                     returned_estimation = coin_values[coin_to_use]    
                
#                 if estimation_against is not None and returned_estimation is None:
#                     coin_to_use = None

#         if answer == USER_ACTION_CONTINUE:
#             if coin_to_use is not None:
#                 break
#             else:
#                 print ('\nPlease select a coin first.\n')

#         if answer == USER_ACTION_QUIT:
#             break

#     return coin_to_use, answer, returned_estimation

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

# def get_user_recipient(question:str, wallet:UserWallet, user_config:dict):
#     """
#     Get the recipient address that we are sending to.

#     If you don't need to check this against existing wallets, then provide an empty dict object for user_config.
#     """

#     while True:
#         answer:str = input(question)
    
#         if answer == USER_ACTION_QUIT:
#             break

#         # We'll assume it was a terra address to start with (by default)
#         recipient_address = answer

#         if isDigit(answer):
#             # Check if this is a wallet number
#             if user_config['wallets'][int(answer)] is not None:
#                 recipient_address = user_config['wallets'][int(answer)]['address']

#         else:
#             # Check if this is a wallet name
#             if len(user_config) > 0:
#                 for user_wallet in user_config['wallets']:
#                     if user_wallet['wallet'].lower() == answer.lower():
#                         recipient_address = user_wallet['address']
#                         break

#         # Figure out if this wallet address is legit
#         is_valid, is_empty = wallet.validateAddress(recipient_address)

#         if is_valid == False and is_empty == True:
#             continue_action = get_user_choice('This wallet seems to be empty - do you want to continue? (y/n) ', [])
#             if continue_action == True:
#                 break

#         if is_valid == True:
#             break

#         print (' 🛎️  This is an invalid address - please check and try again.')

#     return recipient_address

def get_user_text(question:str, max_length:int, allow_blanks:bool) -> str:
    """
    Get a text string from the user - must be less than a definied length
    """

    while True:    
        answer = input(question).strip(' ')

        if len(answer) > max_length:
            print (f' 🛎️  The length must be less than {max_length}')
        elif len(answer) == 0 and allow_blanks == False:
            print (f' 🛎️  This value cannot be blank or empty')
        else:
            break

    return str(answer)

# def get_user_number(question:str, params:dict):
#     """
#     Get ther user input - must be a number.
#     """ 
    
#     empty_allowed:bool = False
#     if 'empty_allowed' in params:
#         empty_allowed = params['empty_allowed']

#     convert_to_uluna = True
#     if 'convert_to_uluna' in params:
#         convert_to_uluna = params['convert_to_uluna']

#     while True:    
#         answer = input(question).strip(' ')

#         if answer == USER_ACTION_QUIT:
#             break

#         if answer == '' and empty_allowed == False:
#             print (f' 🛎️  The value cannot be blank or empty')
#         else:

#             if answer == '' and empty_allowed == True:
#                 break

#             is_percentage = isPercentage(answer)

#             if 'percentages_allowed' in params and is_percentage == True:
#                 answer = answer[0:-1]

#             if isDigit(answer):

#                 if 'percentages_allowed' in params and is_percentage == True:
#                     if int(answer) > params['min_number'] and int(answer) <= 100:
#                         break
#                 elif 'max_number' in params:
#                     if 'min_equal_to' in params and (float(answer) >= params['min_number'] and float(answer) <= params['max_number']):
#                         break
#                     elif (float(answer) > params['min_number'] and float(answer) <= params['max_number']):
#                         break
#                 elif 'max_number' in params and float(answer) > params['max_number']:
#                     print (f" 🛎️  The amount must be less than {params['max_number']}")
#                 elif 'min_number' in params:
                    
#                     if 'min_equal_to' in params:
#                         if float(answer) < params['min_number']:
#                             print (f" 🛎️  The amount must be greater than (or equal to) {params['min_number']}")
#                         else:
#                             break
#                     else:
#                         if float(answer) <= params['min_number']:
#                             print (f" 🛎️  The amount must be greater than {params['min_number']}")
#                         else:
#                             break
#                 else:
#                     # This is just a regular number that we'll accept
#                     if is_percentage == False:
#                         break

#     if answer != '' and answer != USER_ACTION_QUIT:
#         if 'percentages_allowed' in params and is_percentage == True:
#             if 'convert_percentages' in params and params['convert_percentages'] == True:
#                 wallet:UserWallet = UserWallet()
#                 answer = float(wallet.convertPercentage(answer, params['keep_minimum'], params['max_number'], params['target_denom']))
#             else:
#                 answer = answer + '%'
#         else:
#             if convert_to_uluna == True:
#                 answer = float(multiply_raw_balance(answer, params['target_denom']))

#     return answer

# def get_fees_from_error(log:str, target_coin:str):
#     """
#     Take the error string and figure out the actual required fee and tax.
#     """

#     required:list = log.split('required:')
#     parts:list    = required[1].split('=')
#     fee_line:str  = parts[1]
#     fee_line:str  = fee_line.replace('(stability): insufficient fee', '').replace('"', '').lstrip(' ') .split('(gas) +')

#     # Build the result coins:
#     fee_coins:Coins      = Coins.from_str(fee_line[0])
#     result_tax_coin:Coin = Coin.from_str(fee_line[1])

#     fee_coin:Coin
#     result_fee_coin:Coin
#     for fee_coin in fee_coins:
#         if fee_coin.denom == target_coin:
#             result_fee_coin = fee_coin
#             break

#     return result_fee_coin, result_tax_coin
    