#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from .wallet import UserWallet

class UserWallets:
    def __init__(self):
        self.file           = None
        self.wallets:dict   = {}
        self.addresses:dict = {}

    def getWallet(self, wallet, user_password):
        #delegation_amount:str = ''
        #threshold:int         = 0

        wallet_item:UserWallet = UserWallet().create(name = wallet['wallet'], address = wallet['address'], seed = wallet['seed'], password = user_password)
        # if 'delegations' in wallet:
        #     if 'redelegate' in wallet['delegations']:
        #         delegation_amount = wallet['delegations']['redelegate']
        #         if 'threshold' in wallet['delegations']:
        #             threshold = wallet['delegations']['threshold']

        #     wallet_item.updateDelegation(delegation_amount, threshold)
        #     wallet_item.has_delegations = True
        # else:
        #     wallet_item.has_delegations = False

        #if 'allow_swaps' in wallet:
        #    wallet_item.allow_swaps = bool(wallet['allow_swaps'])

        wallet_item.validated = wallet_item.validateWallet()
    
        self.wallets[wallet['wallet']] = wallet_item

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
                #delegation_amount:str = ''
                #threshold:int         = 0

                wallet_item:UserWallet = UserWallet().create(name = wallet['wallet'], address = wallet['address'], seed = wallet['seed'], password = user_password)

                # if 'delegations' in wallet:
                #     if 'redelegate' in wallet['delegations']:
                #         delegation_amount = wallet['delegations']['redelegate']
                #         if 'threshold' in wallet['delegations']:
                #             threshold = wallet['delegations']['threshold']

                #     wallet_item.updateDelegation(delegation_amount, threshold)
                #     wallet_item.has_delegations = True
                # else:
                #     wallet_item.has_delegations = False

                #if 'allow_swaps' in wallet:
                #    wallet_item.allow_swaps = bool(wallet['allow_swaps'])

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

        return self
    
    def getAddresses(self) -> dict:
        """
        Return the dictionary of addresses.
        No validation or anything fancy is done here.
        """

        return self.addresses
        
    def getWallets(self, validate:bool) -> dict:
        """
        Return the dictionary of wallets.
        If validate = True, then only return validated wallets which are known to have a valid seed.
        """

        if validate == True:
            validated_wallets:dict = {}
            for wallet_name in self.wallets:
                wallet:UserWallet = self.wallets[wallet_name]
                
                if wallet.validated == True:
                    validated_wallets[wallet_name] = wallet
        else:
            validated_wallets = self.wallets
       
        return validated_wallets
    