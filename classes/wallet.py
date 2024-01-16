#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import cryptocode
import json
import requests
import time
import traceback

from datetime import datetime
from dateutil.tz import tz

from classes.common import (
    coin_list,
    divide_raw_balance,
    getPrecision,
    get_user_choice,
    isDigit,
    isPercentage,
    multiply_raw_balance
)
    
from constants.constants import (
    BASE_SMART_CONTRACT_ADDRESS,
    CHAIN_DATA,
    FULL_COIN_LOOKUP,
    SEARCH_RETRY_COUNT,
    UBASE,
    ULUNA,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
    UUSD,
    WITHDRAWAL_REMAINDER,
)

from classes.swap_transaction import SwapTransaction
from classes.terra_instance import TerraInstance
from terra_classic_sdk.core.staking import UnbondingDelegation

from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.api.distribution import Rewards
from terra_classic_sdk.client.lcd.params import PaginationOptions
from terra_classic_sdk.client.lcd.wallet import Wallet
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.staking.data.delegation import Delegation
from terra_classic_sdk.core.staking.data.validator import Validator
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey
class UserWallet:
    def __init__(self):
        self.address:str        = ''
        self.balances:dict      = None
        self.delegations:dict   = {}
        self.denom:str          = ''
        self.denom_traces:dict  = {}
        self.undelegations:dict = {}
        self.name:str           = ''
        self.pools:dict         = {}
        self.prefix:str         = ''
        self.seed:str           = ''
        self.terra:LCDClient    = None
        self.validated: bool    = False
        
    def __iter_delegator_result__(self, delegator:Delegation) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about the delegator and validator etc
        delegator_address:str       = delegator.delegation.delegator_address
        validator_address:str       = delegator.delegation.validator_address
        validator_details:Validator = self.terra.staking.validator(validator_address)
        validator_name:str          = validator_details.description.moniker
        validator_commission:float  = float(validator_details.commission.commission_rates.rate)
        
        # Get the delegated amount:
        balance_denom:str    = delegator.balance.denom
        balance_amount:float = delegator.balance.amount

        # Get any rewards
        rewards:Rewards   = self.terra.distribution.rewards(delegator_address)
        reward_coins:dict = coin_list(rewards.rewards[validator_address], {})
        
        # Make the commission human-readable
        validator_commission = round(validator_commission * 100, 2)

        # Set up the object with the details we're interested in
        if balance_amount > 0:
            self.delegations[validator_name] = {
                'balance_amount': balance_amount, 
                'balance_denom':  balance_denom, 
                'commission':     validator_commission, 
                'delegator':      delegator_address, 
                'rewards':        reward_coins, 
                'validator':      validator_address, 
                'validator_name': validator_name
            }

    def __iter_undelegation_result__(self, undelegation:UnbondingDelegation) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about the delegator and validator etc
        delegator_address:str = undelegation.delegator_address
        validator_address:str = undelegation.validator_address
        entries:list          = []

        for entry in undelegation.entries:
            entries.append({'balance': entry.balance, 'completion_time': entry.completion_time.strftime('%m/%d/%Y')})
       
        # Get the total balance from all the entries
        balance_total:int = 0
        for entry in entries:
            balance_total += entry['balance']

        # Set up the object with the details we're interested in
        self.undelegations[validator_address] = {
            'balance_amount':    balance_total, 
            'delegator_address': delegator_address, 
            'validator_address': validator_address, 
            'entries':           entries
        }
    
    def convertPercentage(self, percentage:float, keep_minimum:bool, target_amount:float, target_denom:str):
        """
        A generic helper function to convert a potential percentage into an actual number.
        """

        percentage:float = float(percentage) / 100
        if keep_minimum == True:
            lunc_amount:float = float((target_amount - WITHDRAWAL_REMAINDER) * percentage)
            if lunc_amount < 0:
                lunc_amount = 0
        else:
            lunc_amount:float = float(target_amount) * percentage
            
        lunc_amount:float = float(str(lunc_amount))
        uluna_amount:int  = int(multiply_raw_balance(lunc_amount, target_denom))
        
        return uluna_amount
    
    def create(self, name:str = '', address:str = '', seed:str = '', password:str = '', denom:str = '') -> Wallet:
        """
        Create a wallet object based on the provided details.
        """

        self.name:str    = name
        self.address:str = address

        if seed != '' and password != '':
            self.seed = cryptocode.decrypt(seed, password)

        # If a denom wasn't provided, then figure it out based on the prefix and the CHAIN_DATA dict
        if denom == '':
            prefix = self.getPrefix(self.address)
            for chain_key in [*CHAIN_DATA]:
                if chain_key != UUSD:
                    # By checking for LCD values, we can support dual prefixes, like LUNC and LUNA
                    if CHAIN_DATA[chain_key]['bech32_prefix'] == prefix and 'lcd_urls' in CHAIN_DATA[chain_key]:
                        denom = chain_key

        self.denom = denom
        
        self.terra = TerraInstance().create(denom)

        return self
    
    def createCoin(self, denom:str, amount: float) -> Coin:
        """
        A basic helper function to create a valid Coin object with the provided details.
        """

        return Coin.from_data({'amount': amount, 'denom': denom})

    
    def denomTrace(self, ibc_address:str):
        """
        Based on the wallet prefix, get the IBC denom trace details for this IBC address
        """
        
        result:list = []

        if ibc_address[0:4] == 'ibc/':
            
            value:str      = ibc_address[4:]
            chain_name:str = CHAIN_DATA[self.denom]['cosmos_name']
            uri:str        = f'https://rest.cosmos.directory/{chain_name}/ibc/apps/transfer/v1/denom_traces/{value}'
            
            if uri not in self.denom_traces:

                retry_count:int = 0
                retry:bool      = True

                while retry == True:
                    try:
                        trace_result:json = requests.get(uri).json()
                    
                        if 'denom_trace' in trace_result:
                            # Store this result for future requests
                            self.denom_traces[uri] = trace_result['denom_trace']
                            # Return this result
                            result = trace_result['denom_trace']
                            break
                        else:
                            break
                    except Exception as err:
                        retry_count += 1
                        if retry_count == 10:
                            print (f'Denom trace error for {uri}:')
                            print (err)
                            retry = False
                            break
                        else:
                            time.sleep(1)
            else:
                result = self.denom_traces[uri]
        
        if len(result) == 0:
            return ibc_address # Not an IBC address we could resolve
        else:
            return result['base_denom']
    
    def formatUluna(self, uluna:float, denom:str, add_suffix:bool = False):
        """
        A generic helper function to convert uluna amounts to LUNC.
        """

        denom         = self.denomTrace(denom)
        precision:int = getPrecision(denom)
        lunc:float    = round(float(divide_raw_balance(uluna, denom)), precision)

        target:str = '%.' + str(precision) + 'f'
        lunc:str   = (target % (lunc)).rstrip('0').rstrip('.')

        if add_suffix:
            lunc = str(lunc) + ' ' + FULL_COIN_LOOKUP[denom]
        
        return lunc
    
    def getBalances(self, target_coin:Coin = None, core_coins_only:bool = False) -> dict:
        """
        Get the balances associated with this wallet.
        If you pass a target_coin Coin object, this will loop until it sees a change on this denomination.

        If you just want the previously fetched balances, use wallet.balances
        """

        if self.terra is not None:
            retry_count:int = 0

            balances:dict = {}
            pools:dict    = {}
            while True:
                
                # Default pagination options
                pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)

                # Get the current balance in this wallet
                result:Coins
                try:
                    result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)

                    # Convert the result into a friendly list
                    for coin in result:
                        if core_coins_only == True:
                            if coin.denom in [ULUNA, UUSD]:
                                balances[coin.denom] = coin.amount
                            
                        else:
                            denom_trace           = self.denomTrace(coin.denom)
                            balances[denom_trace] = coin.amount
                        
                            # We only get pools if the entire coin list is requested
                            if denom_trace[0:len('gamm/pool/')] == 'gamm/pool/':
                                pool_id = denom_trace[len('gamm/pool/'):]
                                pools[int(pool_id)] = coin.amount

                    # Go through the pagination (if any)
                    while pagination['next_key'] is not None:
                        pagOpt.key         = pagination["next_key"]
                        result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)
                        
                        # Convert the result into a friendly list
                        for coin in result:
                            if core_coins_only == True:
                                if coin.denom in [ULUNA, UUSD]:
                                    balances[coin.denom] = coin.amount
                            else:
                                denom_trace           = self.denomTrace(coin.denom)
                                balances[denom_trace] = coin.amount

                                # We only get pools if the entire coin list is requested
                                if denom_trace[0:len('gamm/pool/')] == 'gamm/pool/':
                                    pool_id = denom_trace[len('gamm/pool/'):]
                                    pools[int(pool_id)] = coin.amount
                    
                except Exception as err:
                    print (f'Pagination error for {self.name}:', err)

                if core_coins_only == False:
                    # Add the extra coins (Base etc)
                    if self.terra is not None and self.terra.chain_id == CHAIN_DATA[ULUNA]['chain_id']:
                        coin_balance = self.terra.wasm.contract_query(BASE_SMART_CONTRACT_ADDRESS, {'balance':{'address':self.address}})
                        if int(coin_balance['balance']) > 0:
                            balances[UBASE] = coin_balance['balance']

                if target_coin is not None:
                    # If the current balance has a higher amount in it than that target coin, then we can exit
                    if target_coin.denom in balances and balances[target_coin.denom] > target_coin.amount:
                        break
                else:
                    # We're not checking a specific coin, we can exit now
                    break

                # Wait for one second and try again
                retry_count += 1
                if retry_count <= SEARCH_RETRY_COUNT:
                    print (f'Target denom not found... attempt {retry_count}/{SEARCH_RETRY_COUNT}')
                    time.sleep(1)
                else:
                    break
        else:
            balances:dict = {}

        self.balances = balances
        self.pools    = pools

        return self.balances
    
    async def getBalancesAsync(self) -> dict:
        """
        An asynchronous wrapper aruond the standard delegation function.
        """

        balances:dict = self.getBalances(core_coins_only = True)

        return balances

    def getCoinSelection(self, question:str, coins:dict, only_active_coins:bool = True, estimation_against:dict = None):
        """
        Return a selected coin based on the provided list.
        """

        label_widths:list = []

        label_widths.append(len('Number'))
        label_widths.append(len('Coin'))
        label_widths.append(len('Balance'))

        if estimation_against is not None:
            label_widths.append(len('Estimation'))
            swap_tx = SwapTransaction().create(self.seed, self.denom)

        coin_list:list   = []
        coin_values:dict = {}

        coin_list.append('')

        for coin in FULL_COIN_LOOKUP:

            if coin in coins:
                coin_list.append(coin)
            elif only_active_coins == False:
                coin_list.append(coin)

            coin_name = FULL_COIN_LOOKUP[coin]
            if len(str(coin_name)) > label_widths[1]:
                label_widths[1] = len(str(coin_name))

            if coin in coins or only_active_coins == False:

                if coin in coins:
                    coin_val = self.formatUluna(coins[coin], coin)

                    if len(str(coin_val)) > label_widths[2]:
                        label_widths[2] = len(str(coin_val))

                if estimation_against is not None:

                    # Set up the swap details
                    swap_tx.swap_amount        = float(self.formatUluna(estimation_against['amount'], estimation_against['denom'], False))
                    swap_tx.swap_denom         = estimation_against['denom']
                    swap_tx.swap_request_denom = coin
                    swap_tx.wallet_denom       = self.denom

                    # Change the contract depending on what we're doing
                    swap_tx.setContract()
                    
                    if coin != estimation_against['denom']:
                        estimated_value:float = swap_tx.swapRate()
                    else:
                        estimated_value:str = None
                    
                    coin_values[coin] = estimated_value
                    
                    if len(str(estimated_value)) > label_widths[3]:
                        label_widths[3] = len(str(estimated_value))

        padding_str:str   = ' ' * 100
        header_string:str = ' Number |'

        if label_widths[1] > len('Coin'):
            header_string += ' Coin' + padding_str[0:label_widths[1] - len('Coin')] + ' |'
        else:
            header_string += ' Coin |'

        if label_widths[2] > len('Balance'):
            header_string += ' Balance ' + padding_str[0:label_widths[2] - len('Balance')] + '|'
        else:
            header_string += ' Balance |'

        if estimation_against is not None:
            if label_widths[3] > len('Estimation'):
                header_string += ' Estimation ' + padding_str[0:label_widths[3] - len('Estimation')] + '|'
            else:
                header_string += ' Estimation |'

        horizontal_spacer = '-' * len(header_string)

        coin_to_use:str           = None
        returned_estimation:float = None    
        answer:str                = False
        coin_index:dict           = {}

        while True:

            count:int = 0

            print ('\n' + horizontal_spacer)
            print (header_string)
            print (horizontal_spacer)

            for coin in FULL_COIN_LOOKUP:

                if coin in coins or estimation_against is not None:
                    count += 1
                    coin_index[FULL_COIN_LOOKUP[coin].lower()] = count
                
                if coin_to_use == coin:
                    glyph = '✅'
                elif estimation_against is not None and estimation_against['denom'] == coin:
                    glyph = '⚪'
                else:
                    glyph = '  '

                count_str =  f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
            
                coin_name = FULL_COIN_LOOKUP[coin]
                if label_widths[1] > len(coin_name):
                    coin_name_str = coin_name + padding_str[0:label_widths[1] - len(coin_name)]
                else:
                    coin_name_str = coin_name

                if coin in coins:
                    coin_val = self.formatUluna(coins[coin], coin)

                    if label_widths[2] > len(str(coin_val)):
                        balance_str = coin_val + padding_str[0:label_widths[2] - len(coin_val)]
                    else:
                        balance_str = coin_val
                else:
                    coin_val    = ''
                    balance_str = coin_val + padding_str[0:label_widths[2] - len(coin_val)]

                if coin in coins or only_active_coins == False:
                    if estimation_against is None:
                        print (f"{count_str}{glyph} | {coin_name_str} | {balance_str}")
                    else:
                        if coin in coin_values:
                            if coin_values[coin] is not None:
                                estimated_str:str = str(("%.6f" % (coin_values[coin])).rstrip('0').rstrip('.'))
                            else:
                                estimated_str = '--'
                        else:
                            estimated_str = ''

                        print (f"{count_str}{glyph} | {coin_name_str} | {balance_str} | {estimated_str}")
        
            print (horizontal_spacer + '\n')

            answer:str = input(question).lower()
            
            # Check if a coin name was provided:
            if answer in coin_index:
                answer = str(coin_index[answer])

            if answer.isdigit() and int(answer) > 0 and int(answer) <= count:
                if estimation_against is not None and estimation_against['denom'] == coin_list[int(answer)]:
                    print ('\nYou can\'t swap to the same coin!')
                else:
                
                    returned_estimation:float = None
                    coin_to_use:str           = coin_list[int(answer)] 

                    if estimation_against is not None:
                        returned_estimation = coin_values[coin_to_use]    
                    
                    if estimation_against is not None and returned_estimation is None:
                        coin_to_use = None

            if answer == USER_ACTION_CONTINUE:
                if coin_to_use is not None:
                    break
                else:
                    print ('\nPlease select a coin first.\n')

            if answer == USER_ACTION_QUIT:
                break

        return coin_to_use, answer, returned_estimation
    
    def getDelegations(self) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

        if self.terra is not None:
            pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
            try:
                result, pagination = self.terra.staking.delegations(delegator = self.address, params = pagOpt)

                delegator:Delegation 
                for delegator in result:
                    self.__iter_delegator_result__(delegator)

                while pagination['next_key'] is not None:
                    pagOpt.key         = pagination['next_key']
                    result, pagination = self.terra.staking.delegations(delegator = self.address, params = pagOpt)

                    delegator:Delegation 
                    for delegator in result:
                        self.__iter_delegator_result__(delegator)
            except:
                print (' 🛎️  Network error: delegations could not be retrieved.')

        return self.delegations
    
    async def getDelegationsAsync(self) -> dict:
        """
        An asynchronous wrapper aruond the standard delegation function.
        """

        delegations:dict = self.getDelegations()

        return delegations
    
    def getDenomByPrefix(self, prefix:str) -> str:
        """
        Go through the supported chains to find the denom for the provided prefix
        """

        result = None
        for key in CHAIN_DATA.keys():
            if CHAIN_DATA[key]['bech32_prefix'] == prefix:
                result = key
                break
            
        return result
    
    def getPrefix(self, address:str) -> str:
        """
        Get the first x (usually 4) letters of the address so we can figure out what network it is
        """

        prefix:str = ''
        for char in address:
            if isDigit(char) == False:
                prefix += char
            else:
                break

        return prefix.lower()
    
    def getProposalVote(self, proposal_id) -> str:
        """
        Get the vote that this wallet made on the supplied proposal id
        """

        vote_result:dict = self.terra.gov.vote(proposal_id, self.address)

        # Get the vote value and convert it
        if 'options' in vote_result:
            vote_value = vote_result['options'][0]['option']
            result:str = None
            if vote_value == 'VOTE_OPTION_UNSPECIFIED':
                result = ''
            elif vote_value == 'VOTE_OPTION_YES':
                result = 'Yes'
            elif vote_value == 'VOTE_OPTION_ABSTAIN':
                result = 'Abstain'
            elif vote_value == 'VOTE_OPTION_NO':
                result = 'No'
            elif vote_value == 'VOTE_OPTION_NO_WITH_VETO':
                result = 'No with veto'
        else:
            result = ''

        return result

    def getSupportedPrefixes(self) -> list:
        """
        Return a list of all the supported prefixes, based on what we can find in the CHAIN_DATA dictionary
        """

        result:list = []
        for denom in CHAIN_DATA:
            result.append(CHAIN_DATA[denom]['bech32_prefix'])

        return result

    def getUbaseUndelegations(self, wallet_address:str) -> list:
        """
        Get the undelegations that are in progress for BASE.

        This returns a list of the active undelegations.
        """

        result:json  = requests.get('https://raw.githubusercontent.com/lbunproject/BASEswap-api-price/main/public/unstaked_plus_hashes.json').json()
        results:list = []
        today        = datetime.now()

        for undelegation in result:
            if datetime.strptime(undelegation['releaseDate'], '%m/%d/%Y') > today:
                if undelegation['sendTo'] == wallet_address:
                    results.append(undelegation)
            else:
                break

        return results
    
    def getUndelegations(self) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

        prefix = self.getPrefix(self.address)
        
        if prefix == 'terra':
            if len(self.undelegations) == 0:
                pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
                try:
                
                    result, pagination = self.terra.staking.unbonding_delegations(delegator = self.address, params = pagOpt)

                    unbonding:UnbondingDelegation
                    for unbonding in result:

                        self.__iter_result__(unbonding)

                    while pagination['next_key'] is not None:

                        pagOpt.key         = pagination['next_key']
                        result, pagination = self.terra.staking.unbonding_delegations(delegator = self.address, params = pagOpt)

                        unbonding:UnbondingDelegation
                        for unbonding in result:
                            self.__iter_undelegation_result__(unbonding)

                except Exception as err:
                    print (' 🛎️  Network error: undelegations could not be retrieved.')
                    print (err)
                    

        # Get any BASE undelegations currently in progress
        base_undelegations       = self.getUbaseUndelegations(self.address)
        undelegated_amount:float = 0
        entries:list             = []
        
        utc_zone = tz.gettz('UTC')
        base_zone = tz.gettz('US/Eastern')

        for base_item in base_undelegations:
            undelegated_amount += base_item['luncNetReleased']

            # Convert the BASE date to a UTC format
            # First, we need to swap it to a d/m/y format
            release_date_bits = base_item['releaseDate'].split('/')
            release_date      = f"{release_date_bits[1]}/{release_date_bits[0]}/{release_date_bits[2]}" 
            base_time         = datetime.strptime(release_date, '%d/%m/%Y')

            # Now give it the timezone that BASE works in
            base_time = base_time.replace(tzinfo = base_zone)
            # Convert time to UTC
            utc_time = base_time.astimezone(utc_zone)
            # Generate UTC time string
            utc_string = utc_time.strftime('%d/%m/%Y')

            entries.append({'balance': multiply_raw_balance(base_item['luncNetReleased'], UBASE), 'completion_time': utc_string})
        
        self.undelegations['base'] = {'balance_amount': multiply_raw_balance(undelegated_amount, UBASE), 'entries': entries}

        return self.undelegations
    
    async def getUnDelegationsAsync(self) -> dict:
        """
        An asynchronous wrapper aruond the standard undelegation function.
        """
        
        undelegations:dict = self.getUndelegations()

        return undelegations
    
    def getUserNumber(self, question:str, params:dict):
        """
        Get ther user input - must be a number.
        """ 
        
        empty_allowed:bool = False
        if 'empty_allowed' in params:
            empty_allowed = params['empty_allowed']

        convert_to_uluna = True
        if 'convert_to_uluna' in params:
            convert_to_uluna = params['convert_to_uluna']

        while True:    
            answer = input(question).strip(' ')

            if answer == USER_ACTION_QUIT:
                break

            if answer == '' and empty_allowed == False:
                print (f' 🛎️  The value cannot be blank or empty')
            else:

                if answer == '' and empty_allowed == True:
                    break

                is_percentage = isPercentage(answer)

                if 'percentages_allowed' in params and is_percentage == True:
                    answer = answer[0:-1]

                if isDigit(answer):

                    if 'percentages_allowed' in params and is_percentage == True:
                        if int(answer) > params['min_number'] and int(answer) <= 100:
                            break
                    elif 'max_number' in params:
                        if 'min_equal_to' in params and (float(answer) >= params['min_number'] and float(answer) <= params['max_number']):
                            break
                        elif (float(answer) > params['min_number'] and float(answer) <= params['max_number']):
                            break
                    elif 'max_number' in params and float(answer) > params['max_number']:
                        print (f" 🛎️  The amount must be less than {params['max_number']}")
                    elif 'min_number' in params:
                        
                        if 'min_equal_to' in params:
                            if float(answer) < params['min_number']:
                                print (f" 🛎️  The amount must be greater than (or equal to) {params['min_number']}")
                            else:
                                break
                        else:
                            if float(answer) <= params['min_number']:
                                print (f" 🛎️  The amount must be greater than {params['min_number']}")
                            else:
                                break
                    else:
                        # This is just a regular number that we'll accept
                        if is_percentage == False:
                            break

        if answer != '' and answer != USER_ACTION_QUIT:
            if 'percentages_allowed' in params and is_percentage == True:
                if 'convert_percentages' in params and params['convert_percentages'] == True:
                    wallet:UserWallet = UserWallet()
                    answer = float(wallet.convertPercentage(answer, params['keep_minimum'], params['max_number'], params['target_denom']))
                else:
                    answer = answer + '%'
            else:
                if convert_to_uluna == True:
                    answer = float(multiply_raw_balance(answer, params['target_denom']))

        return answer
    
    def getUserRecipient(self, question:str, user_config:dict):
        """
        Get the recipient address that we are sending to.

        If you don't need to check this against existing wallets, then provide an empty dict object for user_config.
        """

        while True:
            answer:str = input(question)
        
            if answer == USER_ACTION_QUIT:
                break

            # We'll assume it was a terra address to start with (by default)
            recipient_address = answer

            if isDigit(answer):
                # Check if this is a wallet number
                if user_config['wallets'][int(answer)] is not None:
                    recipient_address = user_config['wallets'][int(answer)]['address']

            else:
                # Check if this is a wallet name
                if len(user_config) > 0:
                    for user_wallet in user_config['wallets']:
                        if user_wallet['wallet'].lower() == answer.lower():
                            recipient_address = user_wallet['address']
                            break

            # Figure out if this wallet address is legit
            is_valid, is_empty = self.validateAddress(recipient_address)

            if is_valid == False and is_empty == True:
                continue_action = get_user_choice('This wallet seems to be empty - do you want to continue? (y/n) ', [])
                if continue_action == True:
                    break

            if is_valid == True:
                break

            print (' 🛎️  This is an invalid address - please check and try again.')

        return recipient_address
    
    def getUserText(self, question:str, max_length:int, allow_blanks:bool) -> str:
        """
        Get a text string from the user - must be less than a definied length.
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

    def newWallet(self, prefix:str):
        """
        Creates a new wallet and returns the seed and address
        """

        mk            = MnemonicKey(prefix = prefix)
        wallet:Wallet = self.terra.wallet(mk)
        
        return mk.mnemonic, wallet.key.acc_address
    
    def validateAddress(self, address:str) -> bool:
        """
        Check that the provided address actually resolves to a terra wallet.
        This only applies to addresses which look like terra addresses.
        """

        prefix:str = self.getPrefix(address)

        # If this is an Osmosis address (or something like that) then we'll just accept it
        if prefix != 'terra':
            return True, False
        
        # We'll run some extra checks on terra addresses
        if address != '':
            try:
                result = self.terra.auth.account_info(address)

                # No need to do anything - if it doesn't return an error then it's valid
                return True, False
            
            except LCDResponseError as err:
                if 'decoding bech32 failed' in err.message:
                    return False, False
                if f'account {address} not found' in err.message:
                    return False, True
                else:
                    return False, False
        else:
            return False, False
        
    def validateWallet(self) -> bool:
        """
        Check that the password does actually resolve against any wallets
        
        Go through each wallet and create it based on the password that was provided
        and then check it against the saved address
        If it's not the same, then the password is wrong or the file has been edited.
        """

        try:
            prefix                   = self.getPrefix(self.address)
            generated_wallet_key     = MnemonicKey(mnemonic=self.seed, prefix = prefix)
            generated_wallet         = self.terra.wallet(generated_wallet_key)
            generated_wallet_address = generated_wallet.key.acc_address
            
            if generated_wallet_address == self.address:
                return True
            else:
                return False
        except:
            return False
    