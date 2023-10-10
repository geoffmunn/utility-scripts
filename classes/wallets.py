#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml

from getpass import getpass
from os.path import exists
from .wallet import UserWallet

from constants.constants import (
    CONFIG_FILE_NAME
)
class UserWallets:
    def __init__(self):
        self.file           = None
        self.wallets:dict   = {}
        self.addresses:dict = {}

    def create(self, yml_file:dict, user_password:str):
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
    
    