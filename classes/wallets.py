#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml

from getpass import getpass
from os.path import exists
from .wallet import UserWallet

from constants.constants import (
    CONFIG_FILE_NAME,
    ULUNA,
    USER_ACTION_ALL,
    USER_ACTION_CLEAR,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
    UUSD
)
class UserWallets:
    def __init__(self):
        self.file           = None
        self.wallets:dict   = {}
        self.addresses:dict = {}

    def create(self, yml_file:dict, user_password:str) -> dict:
        """
        Create a dictionary of wallets. Each wallet is a Wallet object.
        """

        if yml_file is None:
            print (' 🛑 No wallets were provided.')
            exit()

        if 'wallets' not in yml_file:
            print (' 🛑 No wallets were provided.')
            exit()

        if yml_file['wallets'] is None:
            print (' 🛑 No wallets were provided.')
            exit()

        for wallet in yml_file['wallets']:

            if 'seed' in wallet:
                wallet_item:UserWallet = UserWallet().create(name = wallet['wallet'], address = wallet['address'], seed = wallet['seed'], password = user_password)

                wallet_item.validated = wallet_item.validateWallet()

                if wallet_item.validated == True:
                    # Add this completed wallet to the list
                    self.wallets[wallet['wallet']] = wallet_item

                    # Add this to the address list as well
                    self.addresses[wallet['wallet']] = wallet_item
            else:
                # It's just an address - add it to the address list
                if 'address' in wallet:
                    wallet_item:UserWallet = UserWallet().create(name = wallet['wallet'], address = wallet['address'])
                    self.addresses[wallet['wallet']] = wallet_item

        return self.wallets
    
    def getAddresses(self) -> dict:
        """
        Return the dictionary of addresses.
        No validation or anything fancy is done here.

        This is used by the send.py file to show an address book of possible addresses
        """

        return self.addresses
    
    def getUserMultiChoice(self, question:str) -> dict|str:
        """
        Get multiple user selections from a list.
        This is a custom function because the options are specific to this list.
        """

        label_widths = []
        label_widths.append(len('Number'))
        label_widths.append(len('Wallet name'))
        label_widths.append(len('LUNC'))
        label_widths.append(len('USTC'))
        label_widths.append(len('Available'))

        for wallet_name in self.wallets:
            wallet:UserWallet = self.wallets[wallet_name]

            # Get the delegations and balances for this wallet
            delegations:dict = wallet.delegations
            balances:dict    = wallet.balances

            # Initialise the reward values
            ulunc_reward:int = 0
            ustc_reward:int  = 0

            if delegations is not None:
                for validator in delegations:
                    if ULUNA in delegations[validator]['rewards']:
                        ulunc_reward += float(wallet.formatUluna(delegations[validator]['rewards'][ULUNA], ULUNA, False))
                                            
                    if UUSD in delegations[validator]['rewards']:
                        ustc_reward += float(wallet.formatUluna(delegations[validator]['rewards'][UUSD], UUSD, False))

            if len(wallet_name) > label_widths[1]:
                label_widths[1] = len(wallet_name)

            if len(str(ulunc_reward)) > label_widths[2]:
                label_widths[2] = len(str(ulunc_reward))

            if len(str(ustc_reward)) > label_widths[3]:
                label_widths[3] = len(str(ustc_reward))

            if ULUNA in balances:
                formatted_val = str(wallet.formatUluna(balances[ULUNA], ULUNA, False))
                if len(formatted_val) > label_widths[4]:
                    label_widths[4] = len(formatted_val)

        padding_str:str   = ' ' * 100
        header_string:str = ' Number |'

        if label_widths[1] > len('Wallet name'):
            header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' '
        else:
            header_string +=  ' Wallet name '

        if label_widths[4] > len('Available'):
            header_string += '| Available' + padding_str[0:label_widths[4] - len('Available')] + ' '
        else:
            header_string += '| Available '

        if label_widths[2] > len('LUNC'):
            header_string += '| LUNC' + padding_str[0:label_widths[2] - len('LUNC')] + ' '
        else:
            header_string += '| LUNC'

        if label_widths[3] > len('USTC'):
            header_string += '| USTC' + padding_str[0:label_widths[3] - len('USTC')] + ' '
        else:
            header_string += '| USTC '

        horizontal_spacer = '-' * len(header_string)

        wallets_to_use:dict = {}
        while True:

            count:int           = 0
            wallet_numbers:dict = {}

            print (horizontal_spacer)
            print (header_string)
            print (horizontal_spacer)

            for wallet_name in self.wallets:
                wallet:UserWallet = self.wallets[wallet_name]
                    
                delegations:dict = wallet.delegations
                balances:dict    = wallet.balances

                count += 1
                # Add this wallet to the lookup list
                wallet_numbers[count] = wallet
                    
                if wallet_name in wallets_to_use:
                    glyph = '✅'
                else:
                    glyph = '  '

                count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
                
                wallet_name_str = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]  

                uluna_reward:int  = 0
                uluna_balance:int = 0
                ustc_reward:int   = 0
                
                if delegations is not None:
                    for validator in delegations:
                        if ULUNA in delegations[validator]['rewards']:
                            uluna_reward += delegations[validator]['rewards'][ULUNA]
                        if UUSD in delegations[validator]['rewards']:
                            ustc_reward += delegations[validator]['rewards'][UUSD]

                lunc_str = str(wallet.formatUluna(uluna_reward, ULUNA, False))
                if label_widths[2] - len(str(lunc_str)) > 0:
                    lunc_str += padding_str[0:(label_widths[2] - (len(str(lunc_str))))]
                
                if ULUNA in wallet.balances:
                    uluna_balance = str(wallet.formatUluna(wallet.balances[ULUNA], ULUNA, False))
                    if label_widths[4] - len(str(uluna_balance)) > 0:
                        uluna_balance += padding_str[0:(label_widths[4] - (len(str(uluna_balance))))]
                else:
                    uluna_balance = padding_str[0:label_widths[4]]

                if UUSD in wallet.balances:
                    ustc_str = str(wallet.formatUluna(ustc_reward, UUSD, False))
                    if label_widths[3] - len(str(ustc_str)) > 0:
                        ustc_str += padding_str[0:(label_widths[3] - (len(str(ustc_str))))]
                else:
                    ustc_str = padding_str[0:label_widths[3]]

                print (f"{count_str}{glyph} | {wallet_name_str} | {uluna_balance} | {lunc_str} | {ustc_str}")
                
            print (horizontal_spacer + '\n')
                
            answer = input(question).lower()
            
            if answer.isdigit() and int(answer) in wallet_numbers:
                key = wallet_numbers[int(answer)].name
                if key not in wallets_to_use:
                    wallets_to_use[key] = wallet_numbers[int(answer)]
                else:
                    wallets_to_use.pop(key)
                
            if answer == USER_ACTION_CLEAR:
                wallets_to_use = {}
            
            if answer == USER_ACTION_ALL:
                wallets_to_use = {}
                for wallet_name in self.wallets:
                    wallets_to_use[wallet_name] = self.wallets[wallet_name]

            if answer == USER_ACTION_CONTINUE:
                break

            if answer == USER_ACTION_QUIT:
                break

        return wallets_to_use, answer
    
    def loadUserWallets(self) -> dict:
        """
        Request the decryption password off the user and load the user_config.yml file based on this
        """

        file_exists = exists(CONFIG_FILE_NAME)

        result:dict = None

        if file_exists:
            decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

            if decrypt_password == '':
                print (' 🛑 Exiting...\n')  
                exit()

            # Now open this file and get the contents
            try:
                with open(CONFIG_FILE_NAME, 'r') as file:
                    user_config = yaml.safe_load(file)

                    print ('Decrypting and validating wallets - please wait...\n')
                    self.create(user_config, decrypt_password)
                    result = self.wallets
                
            except:
               print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script.')
        else:
            print (' 🛑 The user_config.yml does not exist - please run configure_user_wallets.py before running this script.')

        return result
    
    