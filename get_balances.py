#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import copy
import yaml

from getpass import getpass

from utility_classes import (
    Wallets,
    Wallet
)

import utility_constants

full_coin_lookup = {
    'uaud': 'AUT',
    'ucad': 'CAT',
    'uchf': 'CHT',
    'ucny': 'CNT',
    'udkk': 'DKT',
    'ueur': 'EUT',
    'ugbp': 'GBT',
    'uhkd': 'HKT',
    'uidr': 'IDT',
    'uinr': 'INT',
    'ujpy': 'JPT',
    'ukrw': 'KRT',
    'uluna': 'LUNC',
    'umnt': 'MNT',
    'umyr': 'MYT',
    'unok': 'NOT',
    'uphp': 'PHT',
    'usdr': 'SDT',
    'usek': 'SET',
    'usgd': 'SGT',
    'uthb': 'THT',
    'utwd': 'TWT',
    'uusd': 'UST'
}
basic_coin_lookup = {
    'uluna': 'LUNC',
    'uusd': 'UST'
}

def strtobool (val):
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
    
def get_user_choice(question:str) -> str|bool:
    """
    Get the user selection for a prompt and convert it to a standard value.
    """

    while True:    
        answer = input(question).lower()
        
        booly = strtobool(answer)
        
        if booly != -1:
            break;
    
    return booly

def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    just_main_coins:bool = get_user_choice('Show just LUNC and USTC? (y/n) ')

    if just_main_coins == True:
        coin_lookup = basic_coin_lookup
    else:
        coin_type = full_coin_lookup

    try:
        with open(utility_constants.CONFIG_FILE_NAME, 'r') as file:
            user_config = yaml.safe_load(file)
    except :
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script')
        exit()

    print ('Decrypting and validating wallets - please wait...')

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)
    
    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    if len(user_wallets) == 0:
        print (' 🛑 This password couldn\'t decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.')
        exit()

    # Now start doing stuff

    balance_coins = {}

    label_widths = []

    label_widths.append(len('Coin'))
    label_widths.append(len('Wallet'))
    label_widths.append(0)

    # First, create a template of all the validators
    validator_template:dict = {'Available': 0}
    validator_column_count = len(label_widths)
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        
        delegations = wallet.getDelegations()

        for validator in delegations:
            
            if validator not in validator_template:
                validator_template.update({validator: ''})

                label_widths.append(0)
                validator_column_count += 1

    # Then, get all the coins we'll be charting (column 1)

    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]
        wallet.getBalances()

        if len(wallet_name) > label_widths[1]:
            label_widths[1] = len(wallet_name)

        for denom in wallet.balances:            
            raw_amount = float(wallet.balances[denom]) / utility_constants.COIN_DIVISOR
            amount = ("%.6f" % (raw_amount)).rstrip('0').rstrip('.')

            if float(amount) > 0:

                if denom in coin_lookup:
                    coin_denom = copy.deepcopy(coin_lookup[denom])

                    if len(coin_denom) > label_widths[0]:
                        label_widths[0] = len(coin_denom)

                    if coin_denom not in balance_coins:
                        balance_coins[coin_denom] = {}

                    if wallet_name not in balance_coins[coin_denom]:
                        balance_coins[coin_denom].update({wallet_name: validator_template})
                
                    cur_vals:dict = copy.deepcopy(balance_coins[coin_denom][wallet_name])
                    cur_vals.update({'Available': amount})
                    
                    if len(str(amount)) > label_widths[2]:
                        label_widths[2]= len(str(amount))

                    cur_wallets:dict = copy.deepcopy(balance_coins[coin_denom])
                    cur_wallets.update({wallet_name: cur_vals})

                    balance_coins.update({coin_denom: cur_wallets})

        delegations = wallet.getDelegations()
        
        for validator in delegations:
            for denom in delegations[validator]['rewards']:
                raw_amount = float(delegations[validator]['rewards'][denom]) / utility_constants.COIN_DIVISOR
                amount = ("%.6f" % (raw_amount)).rstrip('0').rstrip('.')

                if denom in coin_lookup:

                    if float(amount) > 0:

                        coin_denom = copy.deepcopy(coin_lookup[denom])

                        if coin_denom not in balance_coins:
                            balance_coins[coin_denom] = {}

                        if wallet_name not in balance_coins[coin_denom]:
                            balance_coins[coin_denom].update({wallet_name: validator_template})
                            
                        cur_vals:dict = copy.deepcopy(balance_coins[coin_denom][wallet_name])
                        cur_vals.update({validator: amount})
                        
                        cur_wallets:dict = copy.deepcopy(balance_coins[coin_denom])
                        cur_wallets.update({wallet_name: cur_vals})

                        balance_coins.update({coin_denom: cur_wallets})

                        # Find the validator column that this applies to:
                        val_count = 0
                        for val_name in validator_template:
                            if val_name == validator:
                                break
                            val_count +=1

                        if len(str(amount)) > label_widths[2 + val_count]:
                            label_widths[2+val_count] = len(str(amount))

                        

    padding_str = ' ' * 100

    if label_widths[0] > len('Coin'):
        header_string = ' Coin' + padding_str[0:label_widths[0]-len('Coin')] + ' |'
    else:
        header_string = ' Coin |'

    if label_widths[1] > len('Wallet'):
        header_string += ' Wallet ' + padding_str[0:label_widths[1]-len('Wallet')] + '|'
    else:
        header_string += ' Wallet |'

    val_count = 1
    for validator in validator_template:
        if label_widths[1 + val_count] >= len(validator):
            header_string += ' ' + validator + ' ' + padding_str[0:label_widths[1 + val_count]-len(validator)] + '|'
        else:
            header_string += ' ' + validator[0:label_widths[1 + val_count]-len(validator)] + ' |' 

        val_count += 1

    horizontal_spacer = '-' * len(header_string)
    
    body_string = ''
    for coin_type in balance_coins:

        current_coin =  ' ' + coin_type + padding_str[0:label_widths[0]-len(coin_type)] + ' |'
        body_string += current_coin

        first = True
        for wallet_name in balance_coins[coin_type]:
            if first == True:
                body_string += ' ' + ((wallet_name + padding_str)[0:label_widths[1]]) + ' |'
            else:
                body_string += padding_str[0:len(current_coin) - 1] + '| ' + ((wallet_name + padding_str)[0:label_widths[1]]) + ' |'

            val_count = 1
            for validator in balance_coins[coin_type][wallet_name]:
                body_string += ' ' +  (((str(balance_coins[coin_type][wallet_name][validator])) + padding_str)[0:label_widths[1 + val_count]]) + ' |'
                val_count += 1

            body_string += '\n'

            first = False

        body_string += horizontal_spacer + '\n'

    print ('\n')
    print (horizontal_spacer)
    print (header_string)
    print (horizontal_spacer)
    print (body_string)

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()