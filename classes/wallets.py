#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import asyncio
import yaml

from getpass import getpass
from os.path import exists

from constants.constants import (
    CONFIG_FILE_NAME,
    ULUNA,
    USER_ACTION_ALL,
    USER_ACTION_CLEAR,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
    UUSD
)

from classes.wallet import UserWallet
class UserWallets:
    def __init__(self):
        self.file           = None
        self.wallets:dict   = {}
        self.addresses:dict = {}

    async def __AsyncLoadBalances(self, user_wallets):
        """
        A special function to load wallet balances in an asynchronous mode.
        """

        async def async_loop(user_wallets, wallet_name):
            wallet:UserWallet = user_wallets[wallet_name]
            await wallet.getBalancesAsync()
            
        coros = [async_loop(user_wallets, wallet_name) for wallet_name in user_wallets]
        await asyncio.gather(*coros)

    async def __AsyncLoadDelegations(self, user_wallets):
        """
        A special function to load wallet delegations and undelegations in an asynchronous mode.
        """

        async def async_loop(user_wallets, wallet_name):
            wallet:UserWallet = user_wallets[wallet_name]
            await wallet.getDelegationsAsync()
            await wallet.getUnDelegationsAsync()
            
        coros = [async_loop(user_wallets, wallet_name) for wallet_name in user_wallets]
        
        await asyncio.gather(*coros)
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
    
    def getUserMultiChoice(self, question:str, options:dict) -> dict|str:
        """
        Get multiple user selections from a list.
        This is a custom function because the options are specific to this list.

        Options are:
        {
          'display': 'balances', 'votes'
          'proposal_id': proposal_id (for use when display = votes)   
        }
        """

        label_widths:list = []
        label_widths.append(len('Number'))
        label_widths.append(len('Wallet name'))

        if options['display'] == 'balances':
            label_widths.append(len('LUNC'))
            label_widths.append(len('USTC'))
            label_widths.append(len('Available'))

        if options['display'] == 'votes':
            label_widths.append(len('Your vote'))

        wallet_votes:dict = {}
        for wallet_name in self.wallets:
            wallet:UserWallet = self.wallets[wallet_name]

            if len(wallet_name) > label_widths[1]:
                label_widths[1] = len(wallet_name)

            if options['display'] == 'balances':
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

                if len(str(ulunc_reward)) > label_widths[2]:
                    label_widths[2] = len(str(ulunc_reward))

                if len(str(ustc_reward)) > label_widths[3]:
                    label_widths[3] = len(str(ustc_reward))

                if balances is not None:
                    if ULUNA in balances:
                        formatted_val = str(wallet.formatUluna(balances[ULUNA], ULUNA, False))
                        if len(formatted_val) > label_widths[4]:
                            label_widths[4] = len(formatted_val)

            if options['display'] == 'votes':
                
                # Get the vote for this proposal
                vote_result = wallet.getProposalVote(options['proposal_id'])

                # Store this so we don't have to check twice
                wallet_votes[wallet_name] = vote_result

                if len(vote_result) > label_widths[2]:
                    label_widths[2] = len(vote_result)

        padding_str:str   = ' ' * 100
        header_string:str = ' Number |'

        if label_widths[1] > len('Wallet name'):
            header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' '
        else:
            header_string +=  ' Wallet name '

        if options['display'] == 'balances':
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

        if options['display'] == 'votes':
            header_string += '| Your vote'

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

                if options['display'] == 'balances':
                    if wallet.balances is not None:
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
                        if lunc_str == '0':
                            lunc_str = ''

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
                            if ustc_str == '0':
                                ustc_str = ''

                            if label_widths[3] - len(str(ustc_str)) > 0:
                                ustc_str += padding_str[0:(label_widths[3] - (len(str(ustc_str))))]
                        else:
                            ustc_str = padding_str[0:label_widths[3]]
                            
                        print (f"{count_str}{glyph} | {wallet_name_str} | {uluna_balance} | {lunc_str} | {ustc_str}")
                    else:
                        print (f"{count_str}{glyph} | {wallet_name_str}")
                else:
                    # Vote display goes here
                    vote_result = wallet_votes[wallet_name]
                    print (f"{count_str}{glyph} | {wallet_name_str} | {vote_result}")

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
    
    def getUserSinglechoice(self, question:str, show_delegations:bool = False):
        """
        Get a single user selection from a list.
        This is a custom function because the options are specific to this list.
        """

        label_widths:dict = []

        label_widths.append(len('Number'))
        label_widths.append(len('Wallet name'))
        label_widths.append(len('LUNC'))
        label_widths.append(len('USTC'))

        if show_delegations == True:
            label_widths.append(len('Delegations'))
            label_widths.append(len('Undelegations'))

            for wallet_name in self.wallets:
                self.wallets[wallet_name].getDelegations()
                self.wallets[wallet_name].getUndelegations()

        for wallet_name in self.wallets:
            if len(wallet_name) > label_widths[1]:
                label_widths[1] = len(wallet_name)

            uluna_val:str = ''
            ustc_val:str  = ''
            if self.wallets[wallet_name].balances is not None:
                if ULUNA in self.wallets[wallet_name].balances:
                    uluna_val = self.wallets[wallet_name].formatUluna(self.wallets[wallet_name].balances[ULUNA], ULUNA)
                    
                if UUSD in self.wallets[wallet_name].balances:
                    ustc_val = self.wallets[wallet_name].formatUluna(self.wallets[wallet_name].balances[UUSD], UUSD)
            
            if len(str(uluna_val)) > label_widths[2]:
                label_widths[2] = len(str(uluna_val))

            if len(str(ustc_val)) > label_widths[3]:
                label_widths[3] = len(str(ustc_val))

            if show_delegations == True:
                # Calculate the delegations and undelegations
                delegations = self.wallets[wallet_name].delegations
                for delegation in delegations:
                    if len(str(self.wallets[wallet_name].formatUluna(delegations[delegation]['balance_amount'], ULUNA, False))) > label_widths[4]:
                        label_widths[4] = len(str(self.wallets[wallet_name].formatUluna(delegations[delegation]['balance_amount'], ULUNA, False)))
                
                undelegations = self.wallets[wallet_name].undelegations
                for undelegation in undelegations:
                    if len(str(self.wallets[wallet_name].formatUluna(undelegations[undelegation]['balance_amount'], ULUNA, False))) > label_widths[5]:
                        label_widths[5] = len(str(self.wallets[wallet_name].formatUluna(undelegations[undelegation]['balance_amount'], ULUNA, False)))

        padding_str:str   = ' ' * 100
        header_string:str = ' Number |'

        if label_widths[1] > len('Wallet name'):
            header_string +=  ' Wallet name' + padding_str[0:label_widths[1] - len('Wallet name')] + ' '
        else:
            header_string +=  ' Wallet name '

        if label_widths[2] > len('LUNC'):
            header_string += '| LUNC' + padding_str[0:label_widths[2] - len('LUNC')] + ' '
        else:
            header_string += '| LUNC '

        if label_widths[3] > len('USTC'):
            header_string += '| USTC'  + padding_str[0:label_widths[3] - len('USTC')] + ' '
        else:
            header_string += '| USTC '

        if show_delegations == True:
            if label_widths[4] > len('Delegations'):
                header_string += '| Delegations'  + padding_str[0:label_widths[4] - len('Delegations')] + ' '
            else:
                header_string += '| Delegations '

            if label_widths[5] > len('Undelegations'):
                header_string += '| Undelegations'  + padding_str[0:label_widths[5] - len('Undelegations')] + ' '
            else:
                header_string += '| Undelegations '

        horizontal_spacer:str = '-' * len(header_string)

        wallets_to_use:dict = {}
        user_wallet:dict    = {}
        
        while True:

            count:int           = 0
            wallet_numbers:dict = {}

            print (horizontal_spacer)
            print (header_string)
            print (horizontal_spacer)

            for wallet_name in self.wallets:
                wallet:UserWallet  = self.wallets[wallet_name]

                count                 += 1
                wallet_numbers[count] = wallet
                    
                if wallet_name in wallets_to_use:
                    glyph = '✅'
                else:
                    glyph = '  '

                count_str:str       =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
                wallet_name_str:str = wallet_name + padding_str[0:label_widths[1] - len(wallet_name)]

                lunc_str:str = ''
                ustc_str:str = ''

                if wallet.balances is not None:
                    if ULUNA in wallet.balances:
                        lunc_str = wallet.formatUluna(wallet.balances[ULUNA], ULUNA, False)
                    
                    if UUSD in wallet.balances:
                        ustc_str = wallet.formatUluna(wallet.balances[UUSD], UUSD, False)
                    
                lunc_str = lunc_str + padding_str[0:label_widths[2] - len(lunc_str)]
                ustc_str = ustc_str + padding_str[0:label_widths[3] - len(ustc_str)]
                
                if show_delegations == True:
                    delegations_balance:float   = 0
                    undelegations_balance:float = 0
                    delegations_str:str         = ''
                    undelegations_str:str       = ''

                    delegations = self.wallets[wallet_name].delegations
                    for delegation in delegations:
                        delegations_balance += float(delegations[delegation]['balance_amount'])
                        
                    delegations_str = str(self.wallets[wallet_name].formatUluna(delegations_balance, ULUNA, False))
                    if delegations_str == '0':
                        delegations_str = ' '

                    #if delegations is not None:
                    #    for delegation in delegations:
                    #        delegations_balance += int(delegations[delegation]['balance_amount'])

                    #delegations_str = str(self.wallets[wallet_name].formatUluna(delegations_balance, ULUNA, False))
                    #if delegations_str == '0':
                    #    delegations_str = ''

                    delegations_str = delegations_str + padding_str[0:label_widths[4] - len(delegations_str)]

                    undelegations = self.wallets[wallet_name].undelegations
                    for undelegation in undelegations:
                        undelegations_balance += float(undelegations[undelegation]['balance_amount'])
                        
                    undelegations_str = str(self.wallets[wallet_name].formatUluna(undelegations_balance, ULUNA, False))
                    if undelegations_str == '0':
                        undelegations_str = ' '

                    undelegations_str = undelegations_str + padding_str[0:label_widths[5] - len(undelegations_str)]                    

                    print (f"{count_str}{glyph} | {wallet_name_str} | {lunc_str} | {ustc_str} | {delegations_str} | {undelegations_str}")
                else:
                    print (f"{count_str}{glyph} | {wallet_name_str} | {lunc_str} | {ustc_str}")
                
            print (horizontal_spacer + '\n')

            answer:str = input(question).lower()
            
            if answer.isdigit() and int(answer) in wallet_numbers:

                wallets_to_use:dict = {}

                key = wallet_numbers[int(answer)].name
                if key not in wallets_to_use:
                    wallets_to_use[key] = wallet_numbers[int(answer)]
                else:
                    wallets_to_use.pop(key)
                
            if answer == USER_ACTION_CONTINUE:
                if len(wallets_to_use) > 0:
                    break
                else:
                    print ('\nPlease select a wallet first.\n')

            if answer == USER_ACTION_QUIT:
                break

        # Get the first (and only) validator from the list
        for item in wallets_to_use:
            user_wallet:UserWallet = wallets_to_use[item]
            break
        
        return user_wallet, answer
        
    def loadUserWallets(self, get_balances:bool = True, get_delegations:bool = False) -> dict:
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

        if get_balances == True:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.__AsyncLoadBalances(self.wallets))

        if get_delegations == True:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.__AsyncLoadDelegations(self.wallets))

        return result
    
    