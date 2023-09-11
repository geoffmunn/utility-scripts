#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import cryptocode
from datetime import datetime, tzinfo
import json
import math
import requests
import time
import yaml
from dateutil.tz import tz

import traceback

from utility_constants import (
    #ASTROPORT_UUSD_TO_UKUJI_ADDRESS,
    #ASTROPORT_UUSD_TO_ULUNA_ADDRESS,
    BASE_SMART_CONTRACT_ADDRESS,
    CHAIN_IDS,
    CHECK_FOR_UPDATES,
    COIN_DIVISOR,
    COIN_DIVISOR_ETH,
    CONFIG_FILE_NAME,
    FULL_COIN_LOOKUP,
    GAS_ADJUSTMENT,
    GAS_ADJUSTMENT_SWAPS,
    GAS_PRICE_URI,
    IBC_ADDRESSES,
    KUJI_SMART_CONTACT_ADDRESS,
    OSMOSIS_POOLS,
    SEARCH_RETRY_COUNT,
    TAX_RATE_URI,
    #TERRASWAP_UKUJI_TO_ULUNA_ADDRESS,
    TERRASWAP_UKRW_TO_ULUNA_ADDRESS,
    TERRASWAP_ULUNA_TO_UUSD_ADDRESS,
    TERRASWAP_UUSD_TO_ULUNA_ADDRESS,
    UATOM,
    UBASE,
    UKUJI,
    ULUNA,
    UOSMO,
    UKRW,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
    UUSD,
    VERSION_URI,
    WETH,
    WITHDRAWAL_REMAINDER    
)

from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.api.distribution import Rewards
from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_classic_sdk.client.lcd.params import PaginationOptions
from terra_classic_sdk.client.lcd.wallet import Wallet
from terra_classic_sdk.core.bank import MsgSend
from terra_classic_sdk.core.broadcast import BlockTxBroadcastResult
from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.distribution.msgs import MsgWithdrawDelegatorReward
from terra_classic_sdk.core.fee import Fee
from terra_classic_sdk.core.ibc import Height
from terra_classic_sdk.core.ibc_transfer import MsgTransfer
from terra_classic_sdk.core.market.msgs import MsgSwap
from terra_classic_sdk.core.osmosis import MsgSwapExactAmountIn
from terra_classic_sdk.core.staking import (
    MsgBeginRedelegate,
    MsgDelegate,
    MsgUndelegate,
    UnbondingDelegation
)
from terra_classic_sdk.core.staking.data.delegation import Delegation
from terra_classic_sdk.core.staking.data.validator import Validator
from terra_classic_sdk.core.tx import Tx
from terra_classic_sdk.core.wasm.msgs import MsgExecuteContract
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.key.mnemonic import MnemonicKey

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
                print (' 🛎️  A new version is available!')
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

def divide_raw_balance(amount:int, denom:str) -> float:
    """
    Return a human-readable amount depending on what type of coin this is.
    """
    result:float = 0

    if denom == WETH:
        result = int(amount) / COIN_DIVISOR_ETH
    else:
        result = int(amount) / COIN_DIVISOR

    return result

def getPrecision(denom:str) -> int:
    """
    Depending on the denomination, return the number of zeros that we need to account for
    """

    if denom == WETH:
        precision:int = str(COIN_DIVISOR_ETH).count('0')
    else:
        precision:int = str(COIN_DIVISOR).count('0')

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
    
def get_coin_selection(question:str, coins:dict, only_active_coins:bool = True, estimation_against:dict = None, wallet:Wallet = False):
    """
    Return a selected coin based on the provided list.
    """

    label_widths = []

    label_widths.append(len('Number'))
    label_widths.append(len('Coin'))
    label_widths.append(len('Balance'))

    if estimation_against is not None:
        label_widths.append(len('Estimation'))
        swaps_tx = wallet.swap().create()

    wallet:Wallet = Wallet()
    coin_list     = []
    coin_values   = {}
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
                coin_val = wallet.formatUluna(coins[coin], coin)

                if len(str(coin_val)) > label_widths[2]:
                    label_widths[2] = len(str(coin_val))

            if estimation_against is not None:

                # Set up the swap details
                swaps_tx.swap_amount        = float(wallet.formatUluna(estimation_against['amount'], estimation_against['denom'], False))
                swaps_tx.swap_denom         = estimation_against['denom']
                swaps_tx.swap_request_denom = coin

                # Change the contract depending on what we're doing
                swaps_tx.setContract()

                if coin != estimation_against['denom']:
                    estimated_value:float = swaps_tx.swapRate()

                else:
                    estimated_value:str   = None
                
                coin_values[coin] = estimated_value
                
                if len(str(estimated_value)) > label_widths[3]:
                    label_widths[3] = len(str(estimated_value))

    padding_str   = ' ' * 100
    header_string = ' Number |'

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

    coin_to_use:str            = None
    returned_estimation:float  = None    
    answer:str                 = False
    coin_index:dict            = {}

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
                coin_val = wallet.formatUluna(coins[coin], coin)

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

        answer = input(question).lower()
        
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

def get_user_recipient(question:str, wallet:Wallet, user_config:dict):
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
        is_valid, is_empty = wallet.validateAddress(recipient_address)

        if is_valid == False and is_empty == True:
            continue_action = get_user_choice('This wallet seems to be empty - do you want to continue? (y/n) ', [])
            if continue_action == True:
                break

        if is_valid == True:
            break

        print (' 🛎️  This is an invalid address - please check and try again.')

    return recipient_address

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

def get_user_number(question:str, params:dict):
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
                wallet:Wallet = Wallet()
                answer = float(wallet.convertPercentage(answer, params['keep_minimum'], params['max_number'], params['target_denom']))
            else:
                answer = answer + '%'
        else:
            if convert_to_uluna == True:
                print ('answer:', answer)
                answer = float(multiply_raw_balance(answer, params['target_denom']))

    return answer

def get_fees_from_error(log:str, target_coin:str):
    """
    Take the error string and figure out the actual required fee and tax.
    """

    required:list = log.split('required:')
    parts:list    = required[1].split('=')
    fee_line:str  = parts[1]
    fee_line:str  = fee_line.replace('(stability): insufficient fee', '').replace('"', '').lstrip(' ') .split('(gas) +')

    # Build the result coins:
    fee_coins:Coins      = Coins.from_str(fee_line[0])
    result_tax_coin:Coin = Coin.from_str(fee_line[1])

    fee_coin:Coin
    result_fee_coin:Coin
    for fee_coin in fee_coins:
        if fee_coin.denom == target_coin:
            result_fee_coin = fee_coin
            break

    return result_fee_coin, result_tax_coin
    
class UserConfig:
    def __init__(self):
        self.user_config = None
        self.file_exists:bool

        try:
            with open(CONFIG_FILE_NAME, 'r') as file:
                self.user_config = yaml.safe_load(file)
                self.file_exists = True
        except:
            self.file_exists = False

    def contents(self) -> str:
        if self.file_exists == True:
            return self.user_config    
        else:
            return ''

class Wallets:
    def __init__(self):
        self.file           = None
        self.wallets:dict   = {}
        self.addresses:dict = {}

    def getWallet(self, wallet, user_password):
        delegation_amount:str = ''
        threshold:int         = 0

        wallet_item:Wallet = Wallet().create(wallet['wallet'], wallet['address'], wallet['seed'], user_password)
        if 'delegations' in wallet:
            if 'redelegate' in wallet['delegations']:
                delegation_amount = wallet['delegations']['redelegate']
                if 'threshold' in wallet['delegations']:
                    threshold = wallet['delegations']['threshold']

            wallet_item.updateDelegation(delegation_amount, threshold)
            wallet_item.has_delegations = True
        else:
            wallet_item.has_delegations = False

        if 'allow_swaps' in wallet:
            wallet_item.allow_swaps = bool(wallet['allow_swaps'])

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
                delegation_amount:str = ''
                threshold:int         = 0

                wallet_item:Wallet = Wallet().create(wallet['wallet'], wallet['address'], wallet['seed'], user_password)

                if 'delegations' in wallet:
                    if 'redelegate' in wallet['delegations']:
                        delegation_amount = wallet['delegations']['redelegate']
                        if 'threshold' in wallet['delegations']:
                            threshold = wallet['delegations']['threshold']

                    wallet_item.updateDelegation(delegation_amount, threshold)
                    wallet_item.has_delegations = True
                else:
                    wallet_item.has_delegations = False

                if 'allow_swaps' in wallet:
                    wallet_item.allow_swaps = bool(wallet['allow_swaps'])

                wallet_item.validated = wallet_item.validateWallet()

                self.wallets[wallet['wallet']] = wallet_item

                # Add this to the address list as well
                self.addresses[wallet['wallet']] = wallet_item
            else:
                # It's just an address - add it to the address list
                if 'address' in wallet:
                    wallet_item:Wallet = Wallet().create(wallet['wallet'], wallet['address'])
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
            validated_wallets = {}
            for wallet_name in self.wallets:
                wallet:Wallet = self.wallets[wallet_name]
                
                if wallet.validated == True:
                    validated_wallets[wallet_name] = wallet
        else:
            validated_wallets = self.wallets
       
        return validated_wallets
    
class Wallet:
    def __init__(self):
        self.address:str               = ''
        self.allow_swaps:bool          = False
        self.balances:dict             = None
        self.delegateTx                = DelegationTransaction()
        self.delegation_details:dict   = None
        self.has_delegations:bool      = False
        self.undelegation_details:dict = None
        self.name:str                  = ''
        self.seed:str                  = ''
        self.sendTx                    = SendTransaction()
        self.swapTx                    = SwapTransaction()
        self.terra:LCDClient           = None
        self.validated: bool           = False
        self.withdrawalTx              = WithdrawalTransaction()
    
    def allowSwaps(self, allow_swaps:bool) -> bool:
        """
        Update the wallet with the allow_swaps status.
        """

        self.allow_swaps = allow_swaps
        
        return True
    
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
    
    def create(self, name:str = '', address:str = '', seed:str = '', password:str = '') -> Wallet:
        """
        Create a wallet object based on the provided details.
        """

        self.name    = name
        self.address = address

        if seed != '' and password != '':
            self.seed = cryptocode.decrypt(seed, password)

        prefix = self.getPrefix(self.address)

        self.terra = TerraInstance().create(prefix)

        return self
    
    def delegate(self):
        """
        Update the delegate class with the data it needs
        It will be created via the create() command
        """

        self.delegateTx.seed     = self.seed
        self.delegateTx.balances = self.balances

        return self.delegateTx
    
    def denomTrace(self, ibc_address:str):
        """
        Based on the wallet prefix, get the IBC denom trace details for this IBC address
        """
        if ibc_address[0:4] == 'ibc/':
            
            value      = ibc_address[4:]
            prefix     = self.getPrefix(self.address)
            chain_name = CHAIN_IDS[prefix]['name']

            try:
                trace_result:json = requests.get(f'https://rest.cosmos.directory/{chain_name}/ibc/apps/transfer/v1/denom_traces/{value}').json()
            
                if 'denom_trace' in trace_result:
                    return trace_result['denom_trace']
                else:
                    return False
            except Exception as err:
                print (f'Denom trace error for {self.name}:')
                print (err)
                return False
        else:
            return False

    def formatUluna(self, uluna:float, denom:str, add_suffix:bool = False):
        """
        A generic helper function to convert uluna amounts to LUNC.
        """

        # if denom == WETH:
        #     accuracy = str(COIN_DIVISOR_ETH).count('0')
        # else:
        #     accuracy = str(COIN_DIVISOR).count('0')
        precision:int = getPrecision(denom)
        
        lunc:float = round(float(divide_raw_balance(uluna, denom)), precision)

        target = '%.' + str(precision) + 'f'
        lunc = (target % (lunc)).rstrip('0').rstrip('.')

        if add_suffix:
            lunc = str(lunc) + ' LUNC'
        
        return lunc
    
    def getBalances(self, clear_cache:bool = False) -> dict:
        """
        Get the balances associated with this wallet.
        """

        if clear_cache == True:
            self.balances = None

        if self.balances is None:
            # Default pagination options
            pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)

            # Get the current balance in this wallet
            balances:dict = {}
            result:Coins
            try:
                result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)

                # Convert the result into a friendly list
                for coin in result:
                    denom_trace = self.denomTrace(coin.denom)
                    if denom_trace == False:
                        balances[coin.denom] = coin.amount
                    else:
                        balances[denom_trace['base_denom']] = coin.amount

                # Go through the pagination (if any)
                while pagination['next_key'] is not None:
                    pagOpt.key         = pagination["next_key"]
                    result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)
                    
                    denom_trace = self.denomTrace(coin.denom)
                    if  denom_trace == False:
                        balances[coin.denom] = coin.amount
                    else:
                        balances[denom_trace['base_denom']] = coin.amount
            except Exception as err:
                print (f'Pagination error for {self.name}:', err)

            # Add the extra coins (Kuji etc)
            if self.terra.chain_id == 'columbus-5':
                #coin_balance = self.terra.wasm.contract_query(KUJI_SMART_CONTACT_ADDRESS, {'balance':{'address':self.address}})
                #if int(coin_balance['balance']) > 0:
                #    balances[UKUJI] = coin_balance['balance']

                coin_balance = self.terra.wasm.contract_query(BASE_SMART_CONTRACT_ADDRESS, {'balance':{'address':self.address}})
                if int(coin_balance['balance']) > 0:
                    balances[UBASE] = coin_balance['balance']

            self.balances = balances

        return self.balances
    
    def getDelegations(self) -> dict:
        """
        Get the delegations associated with this wallet address.
        The results are cached so if the list is refreshed then it is much quicker.
        """
        
        if self.has_delegations == True:
            if self.delegation_details is None:
                self.delegation_details = Delegations().create(self.address)

        return self.delegation_details
    
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
    
    def getUndelegations(self) -> dict:
        """
        Get the undelegations associated with this wallet address.
        The results are cached so if the list is refreshed then it is much quicker.
        """

        if self.undelegation_details is None:
            self.undelegation_details = Undelegations().create(self.address, self.balances)

        return self.undelegation_details
    
    def newWallet(self):
        """
        Creates a new wallet and returns the seed and address
        """

        mk            = MnemonicKey()
        wallet:Wallet = self.terra.wallet(mk)
        
        return mk.mnemonic, wallet.key.acc_address

    def send(self):
        """
        Update the send class with the data it needs.
        It will be created via the create() command.
        """

        self.sendTx.seed     = self.seed
        self.sendTx.balances = self.balances

        return self.sendTx
    
    def swap(self):
        """
        Update the swap class with the data it needs.
        It will be created via the create() command.
        """

        self.swapTx.seed     = self.seed
        self.swapTx.balances = self.balances

        return self.swapTx
    
    def updateDelegation(self, amount:str, threshold:int) -> bool:
        """
        Update the delegation details with the amount and threshold details.
        """

        self.delegations = {'delegate': amount, 'threshold': threshold}

        return True
    
    def validateAddress(self, address:str) -> bool:
        """
        Check that the provided address actually resolves to a terra wallet.
        This only applies to addresses which look like terra addresses.
        """

        prefix = self.getPrefix(address)

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
    
    def withdrawal(self):
        """
        Update the withdrawal class with the data it needs.
        It will be created via the create() command.
        """

        self.withdrawalTx.seed     = self.seed
        self.withdrawalTx.balances = self.balances

        return self.withdrawalTx
    
class TerraInstance:
    def __init__(self):
        self.gas_adjustment = float(GAS_ADJUSTMENT)
        self.terra          = None
        
    def create(self, prefix:str = 'terra') -> LCDClient:
        """
        Create an LCD client instance and store it in this object.
        """
        
        if prefix in CHAIN_IDS:
            self.chain_id = CHAIN_IDS[prefix]['chain_id']
            self.url      = CHAIN_IDS[prefix]['lcd_urls'][0]

            if self.chain_id == 'osmosis-1':
                gas_prices = '1uosmo,1uluna'
            else:
                gas_prices = None

            terra:LCDClient = LCDClient(
                chain_id       = self.chain_id,
                gas_adjustment = float(self.gas_adjustment),
                url            = self.url,
                gas_prices     = gas_prices
            )

            self.terra = terra
        
        return self.terra

    def instance(self) -> LCDClient:
        """
        Return the LCD client instance that we have created.
        """
        return self.terra
    
class Delegations(Wallet):

    def __init__(self):
        self.delegations:dict = {}

    def __iter_result__(self, terra:LCDClient, delegator:Delegation) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about the delegator and validator etc
        delegator_address:str       = delegator.delegation.delegator_address
        validator_address:str       = delegator.delegation.validator_address
        validator_details:Validator = terra.staking.validator(validator_address)
        validator_name:str          = validator_details.description.moniker
        validator_commission:float  = float(validator_details.commission.commission_rates.rate)
        
        # Get the delegated amount:
        balance_denom:str    = delegator.balance.denom
        balance_amount:float = delegator.balance.amount

        # Get any rewards
        rewards:Rewards   = terra.distribution.rewards(delegator_address)
        reward_coins:dict = coin_list(rewards.rewards[validator_address], {})
        
        # Make the commission human-readable
        validator_commission = round(validator_commission * 100, 2)

        # Set up the object with the details we're interested in
        if balance_amount > 0:
            self.delegations[validator_name] = {'balance_amount': balance_amount, 'balance_denom': balance_denom, 'commission': validator_commission, 'delegator': delegator_address, 'rewards': reward_coins, 'validator': validator_address,  'validator_name': validator_name}
        
    def create(self, wallet_address:str) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

        prefix = self.getPrefix(wallet_address)

        if prefix == 'terra':
            if len(self.delegations) == 0:
                terra = TerraInstance().create()

                pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
                try:
                    result, pagination = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

                    delegator:Delegation 
                    for delegator in result:
                        self.__iter_result__(terra, delegator)

                    while pagination['next_key'] is not None:

                        pagOpt.key         = pagination['next_key']
                        result, pagination = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

                        delegator:Delegation 
                        for delegator in result:
                            self.__iter_result__(terra, delegator)
                except:
                    print (' 🛎️  Network error: delegations could not be retrieved.')

        return self.delegations
    
class Undelegations(Wallet):

    def __init__(self):
        self.undelegations:dict = {}

    def __iter_result__(self, undelegation:UnbondingDelegation) -> dict:
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
        self.undelegations[validator_address] = {'balance_amount': balance_total, 'delegator_address': delegator_address, 'validator_address': validator_address, 'entries': entries}
 
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
    
    def create(self, wallet_address:str, balances:dict) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

        prefix = self.getPrefix(wallet_address)

        if prefix == 'terra':
            if len(self.undelegations) == 0:
                terra = TerraInstance().create()

                pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
                try:
                
                    result, pagination = terra.staking.unbonding_delegations(delegator = wallet_address, params = pagOpt)

                    unbonding:UnbondingDelegation
                    for unbonding in result:

                        self.__iter_result__(unbonding)

                    while pagination['next_key'] is not None:

                        pagOpt.key         = pagination['next_key']
                        result, pagination = terra.staking.unbonding_delegations(delegator = wallet_address, params = pagOpt)

                        unbonding:UnbondingDelegation
                        for unbonding in result:
                            self.__iter_result__(unbonding)

                except Exception as err:
                    print (err)
                    print (' 🛎️  Network error: undelegations could not be retrieved.')

        # Get any BASE undelegations currently in progress
        if 'ubase' in balances:
            base_undelegations       = self.getUbaseUndelegations(wallet_address)
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

class Validators():

    def __init__(self):        
        self.validators:dict            = {}
        self.sorted_validators:dict     = {}
        self.validators_by_address:dict = {}

    def __iter_result__(self, validator:Validator) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about validator
        commission       = validator.commission
        details          = validator.description.details
        identity         = validator.description.identity
        is_jailed        = validator.jailed
        moniker          = validator.description.moniker
        operator_address = validator.operator_address
        status           = validator.status
        token_count      = validator.tokens
        unbonding_time   = validator.unbonding_time
        
        commision_rate   = int(commission.commission_rates.rate * 100)

        self.validators[moniker] = {'commission': commision_rate, 'details': details, 'identity': identity, 'is_jailed': is_jailed, 'moniker': moniker, 'operator_address': operator_address, 'status': status, 'token_count': token_count, 'unbonding_time': unbonding_time, 'voting_power': 0}
        
    def create(self) -> dict:
        """
        Create a dictionary of information about the validators that are available.
        """

        terra = TerraInstance().create()

        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        result, pagination       = terra.staking.validators(params = pagOpt)

        validator:Validator
        for validator in result:
            self.__iter_result__(validator)

        while pagination['next_key'] is not None:

            pagOpt.key         = pagination['next_key']
            result, pagination = terra.staking.validators(params = pagOpt)
            
            validator:Validator
            for validator in result:
                self.__iter_result__(validator)

        # Go through each validator and create an ordered list
        sorted_validators:dict = {}

        # Calculate the voting power for each validator:
        coin_total = 0
        for validator in self.validators:
            coin_total += int(self.validators[validator]['token_count'])

        for validator in self.validators:

            moniker = self.validators[validator]['moniker']

            self.validators[validator]['voting_power'] = (int(self.validators[validator]['token_count']) / coin_total) * 100

            key = self.validators[validator]['token_count']
            if key not in sorted_validators:
                sorted_validators[moniker] = {}
            
            current:dict               = sorted_validators[moniker]
            current[moniker]           = self.validators[validator]['voting_power']
            sorted_validators[moniker] = key

        sorted_list:list = sorted(sorted_validators.items(), key=lambda x:x[1], reverse=True)[0:len(sorted_validators)]
        sorted_validators = dict(sorted_list)

        # Populate the sorted list with the actual validators
        for validator in sorted_validators:
            sorted_validators[validator] = self.validators[validator]
            self.validators_by_address[self.validators[validator]['operator_address']] = self.validators[validator]

        self.sorted_validators = sorted_validators

        return self.validators

class TransactionCore():
    """
    The core class for all transactions.
    """

    def __init__(self):
        
        self.balances:dict                           = {}
        self.broadcast_result:BlockTxBroadcastResult = None
        self.current_wallet:Wallet                   = None
        self.fee:Fee                                 = None
        self.gas_list:json                           = None
        self.gas_price_url:str                       = None
        self.height:int                              = None
        self.seed:str                                = ''
        self.sequence:int                            = None
        self.tax_rate:json                           = None
        self.terra:LCDClient                         = None
        self.transaction:Tx                          = None
        
        # Initialise the basic variables:
        self.gas_price_url = GAS_PRICE_URI
        # The gas list and tax rate values will be updated when the class is properly created
        
    def broadcast(self) -> BlockTxBroadcastResult:
        """
        A core broadcast function for all transactions.
        It will wait until the transaction shows up in the search function before finishing.
        """

        try:
            result:BlockTxBroadcastResult = self.terra.tx.broadcast(self.transaction)    
        except Exception as err:
            print (' 🛑 A broadcast error occurred.')
            print (err)
            result:BlockTxBroadcastResult = None

        self.broadcast_result:BlockTxBroadcastResult = result

        if result is not None:
            code:int = None

            try:
                code = self.broadcast_result.code
            except:
                print ('Error getting the code attribute')
            
            if code is not None and code != 0:
                # Send this back for a retry with a higher gas adjustment value
                return self.broadcast_result
            else:
                # Find the transaction on the network and return the result
                try:
                    transaction_confirmed = self.findTransaction()

                    if transaction_confirmed == True:
                        print ('This transaction should be visible in your wallet now.')
                    else:
                        print ('The transaction did not appear. Future transactions might fail due to a lack of expected funds.')
                except Exception as err:
                    print (err)

        return self.broadcast_result
            
    def calculateFee(self, requested_fee:Fee, specific_denom:str = '') -> Fee:
        """
        Calculate the fee based on the provided information and what coins are available.
        This function prefers to pay in minor coins first, followed by uluna, and then ustc.

        If desired, the fee can specifically be uusd.
        """

        other_coin_list:list      = []
        has_uluna:int             = 0
        has_uusd:int              = 0
        specific_denom_amount:int = 0

        coin:Coin
        for coin in requested_fee.amount:
            #print ('requested fee coin:', coin)
            # if coin.denom == 'uosmo':
            
            #     print ('ALERT: THIS IS USING THE OSMO FEE CONVERSION')
            #     print ('PLEASE DOUBLE CHECK THAT THIS WORKS - IT IS SET SPECIFICALLY FOR OSMO->LUNC')
            #     # We need to convert OSMO to LUNC for the fee
            #     prices:json = self.getPrices(self.swap_denom, self.swap_request_denom)

            #     # Calculate the LUNC fee
            #     # (osmosis amount * osmosis unit cost) / lunc price
            #     uluna_fee_value = int(math.ceil((coin.amount * prices['to']) / prices['from']))

            #     # Update the requested fee object:
            #     requested_fee.amount    = Coins({Coin('ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0', uluna_fee_value)})
            #     #requested_fee.gas_limit = requested_fee.gas_limit * 1

            #     print ('new amount:', requested_fee.amount)
            #     return requested_fee
            # else:
            if coin.denom in self.balances and int(self.balances[coin.denom]) >= int(coin.amount):

                if coin.denom == UUSD:
                    has_uusd = coin.amount
                elif coin.denom == ULUNA:
                    has_uluna = coin.amount
                else:
                    other_coin_list.append(coin)

                if coin.denom == specific_denom:
                    specific_denom_amount = coin.amount

        if has_uluna > 0 or has_uusd > 0 or len(other_coin_list) > 0:
            
            if len(other_coin_list) > 0:
                requested_fee.amount = Coins({Coin(other_coin_list[0].denom, other_coin_list[0].amount)})
            elif has_uluna > 0:
                requested_fee.amount = Coins({Coin(ULUNA, has_uluna)})
            else:
                requested_fee.amount = Coins({Coin(UUSD, has_uusd)})

            # Override the calculations if we've been told to use uusd or something else
            if specific_denom != '':
                requested_fee.amount = Coins({Coin(specific_denom, specific_denom_amount)})
        else:
            print ('Not enough funds to pay for delegation!')

        return requested_fee

    def findTransaction(self) -> bool:
        """
        Do a search for any transaction with the current tx hash.
        If it can't be found within 10 attempts, then give up.
        """

        # Store the current block here - needed for transaction searches
        self.height = self.terra.tendermint.block_info()['block']['header']['height']

        transaction_found:bool = False

        result:dict = self.terra.tx.search([
            ("message.sender", self.current_wallet.key.acc_address),
            ("message.recipient", self.current_wallet.key.acc_address),
            ('tx.hash', self.broadcast_result.txhash),
            ('tx.height', self.height)
        ])

        retry_count = 0
        while True:
            if len(result['txs']) > 0 and int(result['pagination']['total']) > 0:
                if result['txs'][0].code == 0:
                    print ('Found the hash!')
                    time.sleep(1)
                    transaction_found = True
                    break
                if result['txs'][0].code == 5:
                    print (' 🛑 A transaction error occurred.')
                    transaction_found = False
                    break

            retry_count += 1

            if retry_count <= SEARCH_RETRY_COUNT:
                print ('Tx hash not found, giving it another go')
                time.sleep(1)
            else:
                break

        return transaction_found

    def gasList(self) -> json:
        """
        Make a JSON request for the gas prices, and store it against this LCD client instance.
        This returns a full list of gas tokens, in JSON format:
        {'uluna': '28.325', 'usdr': '0.52469', 'uusd': '0.75', 'ukrw': '850.0', 'umnt': '2142.855', 'ueur': '0.625', 'ucny': '4.9', 'ujpy': '81.85', 'ugbp': '0.55', 'uinr': '54.4', 'ucad': '0.95', 'uchf': '0.7', 'uaud': '0.95', 'usgd': '1.0', 'uthb': '23.1', 'usek': '6.25', 'unok': '6.25', 'udkk': '4.5', 'uidr': '10900.0', 'uphp': '38.0', 'uhkd': '5.85', 'umyr': '3.0', 'utwd': '20.0'}

        If you only want gas in a particular coin, then pass the gas item like this: {'uluna': self.gas_list['uluna']}
        """

        if self.gas_list is None:
            try:
                if self.gas_price_url is not None:
                    gas_list:json = requests.get(self.gas_price_url).json()
                    self.gas_list = gas_list
                else:
                    print (' 🛑 No gas price URL set at self.gas_price_url')
                    exit()
            except:
                print (' 🛑 Error getting gas prices')
                print (requests.get(self.gas_price_url).content)
                exit()

        return self.gas_list
    
    def getPrices(self, from_denom:str, to_denom:str) -> json:
        """
        Get the current USD prices for two different coins.
        From: swap_denom
        To: request_denom

        If the link doesn't work, we'll try 10 times
        """

        retry_count:int  = 0
        retry:bool       = True
        prices:json      = {}
        from_price:float = None
        to_price:float   = None

        # Get the chains that we are using
        from_id:dict = self.getChainByDenom(from_denom)
        to_id:dict   = self.getChainByDenom(to_denom)

        if from_id != False and to_id != False:
            while retry == True:
                try:
                    prices:json = requests.get(f"https://api-indexer.keplr.app/v1/price?ids={from_id['name2']},{to_id['name2']}&vs_currencies=usd").json()

                    # Exit the loop if this hasn't returned an error
                    retry = False

                except Exception as err:
                    retry_count += 1
                    if retry_count == 10:
                        print (' 🛑 Error getting coin prices')
                        print (err)

                        retry = False
                        exit()
                    else:
                        time.sleep(1)

            from_price:float = prices[from_id['name2']]['usd']
            to_price:float   = prices[to_id['name2']]['usd']
        
        return {'from':from_price, 'to': to_price}
    
    def getChainByDenom(self, denom) -> dict:
        """
        Return the chain item that matches the provided denom
        """

        result = False
        for chain in CHAIN_IDS:
            if CHAIN_IDS[chain]['denom'] == denom:
                result = CHAIN_IDS[chain]
                break

        return result
        
    def readableFee(self) -> str:
        """
        Return a description of the fee for the current transaction.
        """
        
        fee_string:str = ''
        if self.fee is not None and self.fee.amount is not None:
            fee_coins:Coins = self.fee.amount

            # Build a human-readable fee description:
            fee_string = 'The fee is '
            first      = True
            fee_coin:Coin

            for fee_coin in fee_coins.to_list():

                amount = divide_raw_balance(fee_coin.amount, fee_coin.denom)

                wallet = Wallet()
                wallet.address = self.sender_address

                ibc_denom = wallet.denomTrace(fee_coin.denom)

                if ibc_denom == False:
                    denom  = FULL_COIN_LOOKUP[fee_coin.denom]
                else:
                    denom = FULL_COIN_LOOKUP[ibc_denom['base_denom']]

                if first == False:
                    fee_string += ', and ' + str(amount) + ' ' + denom
                else:
                    fee_string += str(amount) + ' ' + denom

                first = False

        return fee_string
    
    def taxRate(self) -> json:
        """
        Make a JSON request for the tax rate, and store it against this LCD client instance.
        """

        if self.tax_rate is None:

            try:
                tax_rate:json = requests.get(TAX_RATE_URI).json()
                self.tax_rate = tax_rate
            except:
                print (' 🛑 Error getting the tax rate')
                print (requests.get(self.gas_price_url).content)
                exit()

        return self.tax_rate

class DelegationTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        self.action:str                = ''
        self.delegator_address:str     = ''
        self.delegated_uluna:int       = 0
        self.sender_address:str        = ''
        self.sender_prefix:str         = ''
        self.sequence:int              = None
        self.validator_address_old:str = ''
        self.validator_address:str     = ''

        super(DelegationTransaction, self).__init__(*args, **kwargs)
        
    def create(self):
        """
        Create a delegation object and set it up with the provided details.
        """

        # Create the terra instance
        self.terra = TerraInstance().create()

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()
        self.tax_rate = self.taxRate()

        return self
    
    def delegate(self) -> bool:
        """
        Make a delegation with the information we have so far.
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            msg = MsgDelegate(
                delegator_address = self.delegator_address,
                validator_address = self.validator_address,
                amount            = Coin(ULUNA, self.delegated_uluna)
            )

            options = CreateTxOptions(
                fee        = self.fee,
                gas        = 'auto',
                gas_prices = self.gas_list,
                msgs       = [msg],
                sequence   = self.sequence
            )

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    # This is code 32:
                    if 'account sequence mismatch' in err.message:
                        self.sequence    = self.sequence + 1
                        options.sequence = self.sequence
                        print (' 🛎️  Boosting sequence number')
                    else:
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 A random error has occurred')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        
        except:
            return False
        
    def redelegate(self):
        """
        Redelegate funds from one validator to another.
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            msgRedel = MsgBeginRedelegate(
                validator_dst_address = self.validator_address,
                validator_src_address = self.validator_address_old,
                delegator_address     = self.delegator_address,
                amount                = Coin(ULUNA, self.delegated_uluna)
            )

            options = CreateTxOptions(
                fee        = self.fee,
                gas        = 'auto',
                gas_prices = self.gas_list,
                msgs       = [msgRedel],
                sequence   = self.sequence
            )

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    if 'account sequence mismatch' in err.message:
                        self.sequence    = self.sequence + 1
                        options.sequence = self.sequence
                        print (' 🛎️  Boosting sequence number')
                    else:
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 A random error has occurred')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        
        except:
            return False 
    
    def simulate(self, action) -> bool:
        """
        Simulate a delegation so we can get the fee details.
        The fee details are saved so the actual delegation will work.
        """

        # Set the fee to be None so it is simulated
        self.fee = None
        if self.sequence is None:
            self.sequence = self.current_wallet.sequence()
        
        # This is a provided function. Depending on the original function, we might be delegating or undelegating
        action()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            self.fee = self.calculateFee(requested_fee)

            return True
        else:
            return False
        
    def undelegate(self):
        """
        Undelegate funds from the provided validator
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            msg = MsgUndelegate(
                delegator_address = self.delegator_address,
                validator_address = self.validator_address,
                amount            = Coin(ULUNA, int(self.delegated_uluna))
            )

            options = CreateTxOptions(
                fee        = self.fee,
                gas        = 'auto',
                gas_prices = self.gas_list,
                msgs       = [msg],
                sequence   = self.sequence
            )

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    if 'account sequence mismatch' in err.message:
                        self.sequence    = self.sequence + 1
                        options.sequence = self.sequence
                        print (' 🛎️  Boosting sequence number')
                    else:
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 A random error has occurred')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        
        except:
           return False
        
class SendTransaction(TransactionCore):
    def __init__(self, *args, **kwargs):

        super(SendTransaction, self).__init__(*args, **kwargs)

        self.account_number:int    = None
        self.amount:int            = 0
        self.block_height:int      = None
        self.denom:str             = ''
        self.fee:Fee               = None
        self.fee_deductables:float = None
        self.gas_limit:str         = 'auto'
        self.is_ibc_transfer:bool  = False
        self.memo:str              = ''
        self.recipient_address:str = ''
        self.recipient_prefix:str  = ''
        self.revision_number:int   = None
        self.sender_address:str    = ''
        self.sender_prefix:str     = ''
        self.sequence:int          = None
        self.source_channel:str    = None
        self.tax:float             = None

    def create(self, prefix:str = 'terra'):
        """
        Create a send object and set it up with the provided details.
        """

        # Create the terra instance
        self.terra = TerraInstance().create(prefix)

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(mnemonic = self.seed, prefix = prefix)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()
        self.tax_rate = self.taxRate()

        return self

    def send(self) -> bool:
        """
        Complete a send transaction with the information we have so far.
        If fee is None then it will be a simulation.
        """

        send_amount = int(self.amount)

        if self.tax is not None:
            if self.fee_deductables is not None:
                if int(send_amount + self.tax) > int(self.balances[self.denom]):
                    send_amount = int(send_amount - self.fee_deductables)

        try:
            tx:Tx = None

            if self.is_ibc_transfer == False:

                if self.denom == UBASE:
                    msg = MsgExecuteContract(
                        sender = self.current_wallet.key.acc_address,
                        contract = BASE_SMART_CONTRACT_ADDRESS,
                        execute_msg = {
                            "transfer": {
                                "amount": str(send_amount),
                                "recipient": self.recipient_address
                            }
                        }
                    )
                else:
                    msg = MsgSend(
                        from_address = self.current_wallet.key.acc_address,
                        to_address   = self.recipient_address,
                        amount       = Coins(str(int(send_amount)) + self.denom)
                    )

                options = CreateTxOptions(
                    fee        = self.fee,
                    gas        = str(self.gas_limit),
                    gas_prices = self.gas_list,
                    memo       = self.memo,
                    msgs       = [msg],
                    sequence   = self.sequence
                )
            else:
                if self.sender_prefix == 'terra':
                    msg = MsgTransfer(
                        source_port       = 'transfer',
                        source_channel    = self.source_channel,
                        token             = Coin(self.denom, send_amount),
                        sender            = self.sender_address,
                        receiver          = self.recipient_address,
                        #timeout_height    = Height(revision_number = 1, revision_height = block_height),                            
                        timeout_height    = Height(revision_number = self.revision_number, revision_height = self.block_height),                            
                        timeout_timestamp = 0
                    )
                    
                    options = CreateTxOptions(
                        fee            = self.fee,
                        gas            = self.gas_limit,
                        #gas_adjustment = 3,
                        gas_prices     = self.gas_list,
                        memo           = self.memo,
                        msgs           = [msg],
                        sequence       = self.sequence
                    )
                else:
                    # OSMO:
                    #print (self.sender_address)
                    #print (self.recipient_address)
                    #print (self.source_channel)
                    msg = MsgTransfer(
                        source_port       = 'transfer',
                        source_channel    = self.source_channel,
                        token = {
                            "amount": str(send_amount),
                            "denom": "ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0" # This is uluna, we only support LUNC at the moment
                        },
                        sender            = self.sender_address,
                        receiver          = self.recipient_address,
                        timeout_height    = Height(revision_number = 6, revision_height = self.block_height),
                        timeout_timestamp = 0
                    )
                                        
                    options = CreateTxOptions(
                        account_number = str(self.account_number),
                        sequence = str(self.sequence),
                        msgs=[msg],
                        fee = self.fee,
                        gas = '7500',
                        fee_denoms = ['uosmo']
                    )

                    exit()

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    if 'account sequence mismatch' in err.message:
                        self.sequence    = self.sequence + 1
                        options.sequence = self.sequence
                        print (' 🛎️  Boosting sequence number')
                    else:
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 A random error has occurred')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        except Exception as err:
            print (' 🛑 A random error has occurred')
            print (err)
            return False
    
    def simulate(self) -> bool:
        """
        Simulate a delegation so we can get the fee details.
        The fee details are saved so the actual delegation will work.

        Outputs:
        self.fee - requested_fee object with fee + tax as separate coins (unless both are lunc)
        self.tax - the tax component
        self.fee_deductables - the amount we need to deduct off the transferred amount

        """

        if self.sequence is None:
            self.sequence = self.current_wallet.sequence()

        if self.account_number is None:
            self.account_number = self.current_wallet.account_number()

        # Perform the swap as a simulation, with no fee details
        self.send()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple
            self.fee = self.calculateFee(requested_fee, ULUNA)
            
            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
            fee_denom    = fee_bit.denom
        
            if self.is_ibc_transfer == False:
                
                # Calculate the tax portion
                if self.denom == UBASE:
                    # No taxes for BASE transfers
                    self.tax = 0
                else:
                    self.tax = int(math.ceil(self.amount * float(self.tax_rate['tax_rate'])))

                # Build a fee object
                if fee_denom == ULUNA and self.denom == ULUNA:
                    new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
                elif self.denom == UBASE:
                    new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})
                else:
                    new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount)), Coin(self.denom, int(self.tax))})
                    
                requested_fee.amount = new_coin
            else:
                # No taxes for IBC transfers
                self.tax = 0

            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            # Store this so we can deduct it off the total amount to swap.
            # If the fee denom is the same as what we're paying the tax in, then combine the two
            # Otherwise the deductible is just the tax value
            # This assumes that the tax is always the same denom as the transferred amount.
            if fee_denom == self.denom:
                self.fee_deductables = int(fee_amount + self.tax)
            elif fee_denom == ULUNA and self.denom == UUSD:
                self.fee_deductables = int(self.tax)
            else:
                self.fee_deductables = int(self.tax * 2)

            return True
        else:
            return False
        
class SwapTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(SwapTransaction, self).__init__(*args, **kwargs)

        self.account_number:int     = None
        self.belief_price           = None
        self.contract               = None
        self.fee_deductables:float  = None
        self.gas_limit:str          = 'auto'
        self.ibc_routes:list        = []
        self.max_spread:float       = 0.01
        self.min_out:int            = None
        self.recipient_address:str  = ''
        self.recipient_prefix:str   = ''
        self.sender_address:str     = ''
        self.sender_prefix:str      = ''
        self.sequence:int           = None
        self.swap_amount:int        = None
        self.swap_denom:str         = None
        self.swap_request_denom:str = None
        self.tax:float              = None
        self.use_market_swap:bool   = False

    def beliefPrice(self) -> float:
        """
        Figure out the belief price for this swap.
        """

        belief_price:float = 0

        if self.contract is not None:
            try:
                if self.swap_denom != UBASE and self.swap_request_denom != UBASE:
                    result = self.terra.wasm.contract_query(self.contract, {"pool": {}})
                
                    parts:dict = {}
                    if 'native_token' in result['assets'][0]['info']:
                        parts[result['assets'][0]['info']['native_token']['denom']] = int(result['assets'][0]['amount'])
                    #else:
                    #    if result['assets'][0]['info']['token']['contract_addr'] == KUJI_SMART_CONTACT_ADDRESS:
                    #        parts[UKUJI] = int(result['assets'][0]['amount'])

                    parts[result['assets'][1]['info']['native_token']['denom']] = int(result['assets'][1]['amount'])

                    contract_swaps:list  = [ULUNA, UKRW, UUSD]#, UKUJI]

                    if self.swap_denom in contract_swaps and self.swap_request_denom in contract_swaps:
                        # Just about all swap types will use this approach:
                        belief_price:float = parts[self.swap_denom] / parts[self.swap_request_denom]
                        
                else:
                    # UBASE does something different
                    result = self.terra.wasm.contract_query(self.contract, {"curve_info": {}})
                    spot_price:float = float(result['spot_price'])
                    if self.swap_request_denom == UBASE:
                        belief_price:float = divide_raw_balance((spot_price * 1.053), UBASE)
                    else:
                        belief_price:float = divide_raw_balance((spot_price - (spot_price * 0.048)), UBASE)

            except Exception as err:
                print (' 🛑 A connection error has occurred')
                print (err)
                return None
           
        self.belief_price = round(belief_price, 18)

        return self.belief_price
    
    def create(self, prefix:str = 'terra'):
        """
        Create a swap object and set it up with the provided details.
        """

        # Create the terra instance
        self.terra = TerraInstance().create(prefix)

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(mnemonic = self.seed, prefix = prefix)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()
        self.tax_rate = self.taxRate()

        return self
    
    def marketSimulate(self):
        """
        Simulate a market swap so we can get the fee details.
        The fee details are saved so the actual market swap will work.
        """

        self.sequence       = self.current_wallet.sequence()
        self.account_number = self.current_wallet.account_number()

        # Bump up the gas adjustment - it needs to be higher for swaps it turns out
        self.terra.gas_adjustment = float(GAS_ADJUSTMENT_SWAPS)

        #Perform the swap as a simulation, with no fee details
        self.marketSwap()
        
        # Get the transaction result
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            self.fee = self.calculateFee(requested_fee)

            return True
        else:
            return False

    def marketSwap(self):
        """
        Make a market swap with the information we have so far.
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            tx_msg = MsgSwap(
                trader     = self.current_wallet.key.acc_address,
                offer_coin = Coin(self.swap_denom, self.swap_amount),
                ask_denom  = self.swap_request_denom
            )

            options = CreateTxOptions(
                fee            = self.fee,
                gas            = self.gas_limit,
                gas_prices     = self.gas_list,
                msgs           = [tx_msg],
                sequence       = self.sequence,
                account_number = str(self.account_number),
                
            )
            
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    if 'account sequence mismatch' in err.message:
                        self.sequence    = self.sequence + 1
                        options.sequence = self.sequence
                        print (' 🛎️  Boosting sequence number')
                    else:
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 A random error has occurred')
                    print (err)
                    break

            self.transaction = tx

            return True
        except:
            return False
        
    def offChainSimulate(self):
        """
        Simulate an offchain swap so we can get the fee details.
        The fee details are saved so the actual market swap will work.
        """

        self.sequence       = self.current_wallet.sequence()
        self.account_number = self.current_wallet.account_number()
        self.ibc_routes     = IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['routes']

        # Figure out the minimum expected coins for this swap:
        #swap_rate:Coin = self.swapRate()

        #swap_fee:float = IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['swap_fee']
        #gas_adjustment = IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['gas_adjustment']
        fee_multiplier:float = float(IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['fee_multiplier'])
        #print ('swap amount before tax:', (swap_rate.amount * 0.995))
        #print ('max spread:', self.max_spread)

        #For each route, conver the current coin to the base price
        # Deduct swap fee
        # deduct slippage
        
        current_amount = self.swap_amount
        current_denom = self.swap_denom
        target_denom = self.swap_request_denom

        print ('starting amount:', current_amount)
        #wallet = Wallet()

        for route in self.ibc_routes:
            print ('--------')
            print ('route:', route)
            # Get the token we want to swap to (what we expect to end up with for this route)
            token_out_denom = OSMOSIS_POOLS[route['pool_id']][current_denom]
            print (f'Swapping {current_denom} to {token_out_denom}')

            # Get the prices for the current denom and the output denom
            coin_prices:json = self.getPrices(current_denom, token_out_denom)
            

            print ('coin prices:', coin_prices)
            
            
            #lunc = ('%.6f' % (lunc)).rstrip('0').rstrip('.')
            #print ('the current value is:', current_value)
            
            # Get the initial base price (no fee deductions)
            base_amount = (current_amount * coin_prices['from']) / coin_prices['to']

            print ('base amount1:', base_amount)
            #step 1: run price conversion
            #step 2: divide by $eth precision
            #Step 3: multiple by Cosmo precision
            #step 4: round to cosmo precision

            #from_precision=getPrecision(current_denom)
            #target_precision= getPrecision(token_out_denom)
            base_amount = divide_raw_balance(base_amount, current_denom)
            base_amount = multiply_raw_balance(base_amount, token_out_denom)
            print ('base amount2:', base_amount)

            #print ('current amount:', current_amount)
            #print ('from price:', coin_prices['from'])
            #print ('to price:', coin_prices['to'])

            #print ('the current denom at this point is:', token_out_denom)
            #print ('the original base amount is', base_amount)
            #test = divide_raw_balance(base_amount, token_out_denom)
            #precision = getPrecision(token_out_denom)
            #target = f'%.{precision}f'
            #test = (target % (test)).rstrip('0').rstrip('.')
            #print (f"We now have {test} of {token_out_denom}")
            
            #print ('This should have a precision of', precision)


            #print ('base price:', base_price)
            #base_price:int = ('%.6f' % (base_price)).rstrip('0').rstrip('.')
            #print ('base price2:', base_price)

            # deduct the swap fee:
            swap_fee:float = float(OSMOSIS_POOLS[route['pool_id']]['swap_fee'])
            print ('swap fee:', swap_fee)
            # Deduct the swap fee
            base_amount_minus_swap_fee:float = float(base_amount) * (1 - swap_fee)

            print ('base price minus swap fee:', base_amount_minus_swap_fee)
            # Deduct the slippage
            base_amount_minus_swap_fee = base_amount_minus_swap_fee * (1 - self.max_spread)

            print ('base price minus slippage:', base_amount_minus_swap_fee)

            print (base_amount_minus_swap_fee)

            # Now we have the new denom and the new value
            current_denom = token_out_denom        
            current_amount = base_amount_minus_swap_fee
            precision = getPrecision(token_out_denom)
            target = f'%.{precision}f'

            test = (target % (current_amount)).rstrip('0').rstrip('.')
            print (f"We now have {test} of {token_out_denom}")
            
            print ('This should have a precision of', precision)
            #target = f'%.{precision}f'
            #print ('initial test value:', ((target % (current_amount)).rstrip('0').rstrip('.')))

            #print (target_denom, precision)
            #current_value = round(current_value, precision)
            #test = divide_raw_balance(current_value, current_denom)
            #test = multiply_raw_balance(test, current_denom)
            #test = current_value / (10 * int(precision))
            #print ('test divided:', test)
            #test = round(test, precision)
            #print ('test rounded:', test)
            
            #print ('fixed value:', ((target % (test)).rstrip('0').rstrip('.')))
            #test = divide_raw_balance(current_value, current_denom)
            
            print ('new current denom:', current_denom)
            print ('current amount:', (target % (current_amount)).rstrip('0').rstrip('.'))

        precision = getPrecision(target_denom)
        print ('precision:', precision)
        current_amount = round(current_amount, precision)
        
        print (('%.6f' % (current_amount)).rstrip('0').rstrip('.'))
        #current_value = 990798716
        print ('swap min:', current_amount)
        # Now do route 2
        # route = self.ibc_routes[1]


        # token_out_denom = OSMOSIS_POOLS[route['pool_id']]['token_out']

        # print (f"Second route, swapping {current_denom} to {token_out_denom}")
        # coin_prices = self.getPrices(current_denom, token_out_denom)
        # # Get the initial base price
        # base_price = (base_price_minus_swap_fee * coin_prices['from']) / coin_prices['to']
        # # deduct the swap fee:
        # swap_fee:float = float(OSMOSIS_POOLS[route['pool_id']]['swap_fee'])
        # # Deduct the swap fee
        # base_price_minus_swap_fee = base_price * (1 - swap_fee)
        # # Deduct the slippage
        # base_price_minus_swap_fee = base_price_minus_swap_fee * (1 - self.max_spread)
        # print (base_price_minus_swap_fee)
        #exit()

        #self.min_out = math.floor((swap_rate.amount * 0.995) * (1 - float(swap_fee)) * (1 - float(self.max_spread)))
        self.min_out = math.floor(current_amount)
        print ('min out:', self.min_out)   
                    
        #self.min_out   = math.floor(swap_rate.amount * (1 - self.max_spread))
        #self.min_out   = math.floor(swap_rate.amount * 0.95)

        self.offChainSwap()

        # Get the transaction result
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee = tx.auth_info.fee

            print ('requested fee:', requested_fee)

            # Get the fee details, but we'll need to make some modifications
            self.fee:Fee  = self.calculateFee(requested_fee)
            print ('calculated fee:', self.fee)
            
            fee_coin:Coin = self.fee.amount.to_list()[0]
            
            # We'll take the returned fee and use that as the gas limit
            #self.gas_limit = math.floor(self.fee.gas_limit * float(gas_adjustment))
            self.gas_limit = self.fee.gas_limit
            
            print ('gas limit:', self.gas_limit)            
            # Now calculate the actual fee
            #(0.007264 * 0.424455) / 0.00006641 = 43.7972496474
            min_uosmo_gas:float = 0.0025
            uosmo_fee:float     = min_uosmo_gas * float(self.gas_limit)

            print ('uosmo fee:', uosmo_fee)
            # Calculate the LUNC fee
            # (osmosis amount * osmosis unit cost) / lunc price
            # For the calculation to work, the 'to' value always needs to be the usomo price
            #if self.swap_denom == ULUNA and self.swap_request_denom == UOSMO:
                #from_denom:str = self.swap_denom
                #to_denom:str = self.swap_request_denom
            #elif self.swap_denom == UOSMO and self.swap_request_denom == ULUNA:
            #    from_denom:str = self.swap_request_denom
            #    to_denom:str = self.swap_denom

            from_denom:str = UOSMO
            to_denom:str = ULUNA

            prices:json    = self.getPrices(from_denom, to_denom)
            print ('prices:', prices)
            #fee_amount:float = float((uosmo_fee * prices['to']) / prices['from'])
            #print ('from:', from_denom)
            #print ('to:', to_denom)

            # OSMO -> LUNC:
            fee_amount:float = float((uosmo_fee * prices['from']) / prices['to'])
            #fee_amount:float = float((uosmo_fee * prices['to']) / prices['from'])

            print ((uosmo_fee * prices['from']))
            print (float((uosmo_fee * prices['from']) / prices['to']))
            
            print ('fee amount:', fee_amount)
            fee_amount = fee_amount * fee_multiplier
            fee_denom:str  = fee_coin.denom
            print ('fee denom:', fee_denom)
            fee_denom:str = 'ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0'

            new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})

            # This will be used by the swap function next time we call it
            self.fee.amount = new_coin

            print ('final fee:', self.fee)
            return True
        else:
            return False
        

    def offChainSwap(self):
        """
        Make an offchain swap with the information we have so far.
        Currently we only support MsgSwapExactAmountIn via the GAMM module.

        If fee is None then it will be a simulation.
        """

        # try:
        
        token_in:Coin   = Coin(IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['token_in'], self.swap_amount)

        tx_msg = MsgSwapExactAmountIn(
            sender               = self.sender_address,
            routes               = self.ibc_routes,
            token_in             = str(token_in),
            token_out_min_amount = str(self.min_out)
        )

        options = CreateTxOptions(
            fee            = self.fee,
            gas            = self.gas_limit,
            gas_adjustment = IBC_ADDRESSES[self.swap_denom][self.swap_request_denom]['gas_adjustment'],
            msgs           = [tx_msg],
            sequence       = self.sequence,
            account_number = self.account_number
        )

        print ('options:', options)
        tx:Tx = self.current_wallet.create_and_sign_tx(options)
        
        self.transaction = tx

        return True

    def setContract(self) -> bool:
        """
        Depending on what the 'from' denom is and the 'to' denom, change the contract endpoint.

        If this is going to use a market swap, then we don't need a contract.
        """
        
        use_market_swap:bool = True
        self.contract        = None
        contract_swaps:list  = [ULUNA, UKRW, UUSD, UBASE]# UKUJI, UBASE]

        if self.swap_denom in contract_swaps and self.swap_request_denom in contract_swaps:

            use_market_swap = False

            if self.swap_denom == ULUNA:
                if self.swap_request_denom == UUSD:
                    self.contract = TERRASWAP_ULUNA_TO_UUSD_ADDRESS
                if self.swap_request_denom == UKRW:
                    self.contract = TERRASWAP_UKRW_TO_ULUNA_ADDRESS
                if self.swap_request_denom == UBASE:
                    self.contract = BASE_SMART_CONTRACT_ADDRESS

            if self.swap_denom == UUSD:
                if self.swap_request_denom == ULUNA:
                    #self.contract = ASTROPORT_UUSD_TO_ULUNA_ADDRESS
                    self.contract = TERRASWAP_UUSD_TO_ULUNA_ADDRESS
                if self.swap_request_denom == UKRW:
                    self.contract = None
                    use_market_swap = True

            if self.swap_denom == UKRW:
                if self.swap_request_denom == ULUNA:
                    self.contract = TERRASWAP_UKRW_TO_ULUNA_ADDRESS
                if self.swap_request_denom == UUSD:
                    self.contract = None
                    use_market_swap = True

            #if self.swap_denom == UUSD:
                #if self.swap_request_denom == UKUJI:
                #    self.contract = ASTROPORT_UUSD_TO_UKUJI_ADDRESS
            #if self.swap_denom == UKUJI:
            #    if self.swap_request_denom == UUSD:
            #        self.contract = ASTROPORT_UUSD_TO_UKUJI_ADDRESS

            if self.swap_denom == UBASE:
                if self.swap_request_denom == ULUNA:
                    self.contract = BASE_SMART_CONTRACT_ADDRESS

        self.use_market_swap = use_market_swap

        return use_market_swap
      
    def simulate(self) -> bool:
        """
        Simulate a delegation so we can get the fee details.
        THIS IS ONLY FOR USTC <-> LUNC SWAPS
        The fee details are saved so the actual delegation will work.

        Outputs:
        self.fee - requested_fee object with fee + tax as separate coins (unless both are lunc)
        self.tax - the tax component
        self.fee_deductables - the amount we need to deduct off the transferred amount

        """

        self.belief_price   = self.beliefPrice()

        self.sequence       = self.current_wallet.sequence()
        self.account_number = self.current_wallet.account_number()
        
        # Perform the swap as a simulation, with no fee details
        self.swap()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple

            self.fee = self.calculateFee(requested_fee, ULUNA)

            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
            fee_denom    = fee_bit.denom

            # Calculate the tax portion 
            if self.swap_denom == UBASE:
                self.tax = None
            else:
                self.tax = int(math.ceil(self.swap_amount * float(self.tax_rate['tax_rate'])))

            # Build a fee object
            if fee_denom == ULUNA and self.swap_denom == ULUNA:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
            if self.swap_denom == UBASE:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})
            else:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount)), Coin(self.swap_denom, int(self.tax))})

            requested_fee.amount = new_coin
            
            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            # Store this so we can deduct it off the total amount to swap.
            # If the fee denom is the same as what we're paying the tax in, then combine the two
            # Otherwise the deductible is just the tax value
            # This assumes that the tax is always the same denom as the transferred amount.
            if fee_denom == self.swap_denom:
                self.fee_deductables = int(fee_amount + self.tax)
            elif fee_denom == ULUNA and self.swap_denom == UUSD:
                self.fee_deductables = int(self.tax)
            elif fee_denom == ULUNA and self.swap_denom == UBASE:
                self.fee_deductables = 0
            #elif fee_denom == UKUJI and self.swap_denom == UUSD:
            #    self.fee_deductables = int(self.tax)
            else:
                if self.tax is not None:
                    self.fee_deductables = int(self.tax * 2)
                else:
                    self.fee_deductables = None

            return True
        else:
            return False
    
    def swap(self) -> bool:
        """
        Make a swap with the information we have so far.
        If fee is None then it will be a simulation.
        """

        if self.belief_price is not None:
            
            if self.fee is not None:
                fee_amount:list = self.fee.amount.to_list()
                fee_coin:Coin   = fee_amount[0]
                fee_denom:str   = fee_coin.denom
            else:
                fee_denom:str   = UUSD

            if fee_denom in self.balances:
                swap_amount = self.swap_amount

                if self.tax is not None:
                   if self.fee_deductables is not None:
                       if int(swap_amount + self.fee_deductables) > int(self.balances[self.swap_denom]):
                           swap_amount = int(swap_amount - self.fee_deductables)

                if self.swap_denom == ULUNA and self.swap_request_denom == UBASE:
                    # We are swapping LUNC for BASE
                    tx_msg = MsgExecuteContract(
                        sender      = self.current_wallet.key.acc_address,
                        contract    = self.contract,
                        execute_msg = {
                            "buy": {"affiliate": ""}
                        },
                        coins       = Coins(str(swap_amount) + self.swap_denom)
                    )
                    options = CreateTxOptions(
                        fee        = self.fee,
                        gas        = 500000,
                        gas_prices = {'uluna': self.gas_list['uluna']},
                        msgs       = [tx_msg],
                        sequence   = self.sequence,
                    )
                elif self.swap_denom == UBASE:
                    # We are swapping BASE back to ULUNA
                    tx_msg = MsgExecuteContract(
                        sender      = self.current_wallet.key.acc_address,
                        contract    = self.contract,
                        execute_msg = {
                            "burn": {"amount": str(swap_amount)}
                        }
                    )
                    options = CreateTxOptions(
                        fee        = self.fee,
                        gas        = 500000,
                        gas_prices = {'uluna': self.gas_list['uluna']},
                        msgs       = [tx_msg],
                        sequence   = self.sequence,
                    )
                else:
                    tx_msg = MsgExecuteContract(
                        sender      = self.current_wallet.key.acc_address,
                        contract    = self.contract,
                        execute_msg = {
                            'swap': {
                                'belief_price': str(self.belief_price),
                                'max_spread': str(self.max_spread),
                                'offer_asset': {
                                    'amount': str(swap_amount),
                                    'info': {
                                        'native_token': {
                                            'denom': self.swap_denom
                                        }
                                    }
                                },
                            }
                        },
                        coins = Coins(str(swap_amount) + self.swap_denom)
                    )

                    options = CreateTxOptions(
                        fee            = self.fee,
                        gas            = 1000000,
                        gas_prices     = self.gas_list,
                        gas_adjustment = 3.6,
                        msgs           = [tx_msg],
                        sequence       = self.sequence,
                    )

                # If we are swapping from lunc to usdt then we need a different fee structure
                if self.swap_denom == ULUNA and self.swap_request_denom == UUSD:
                    options.fee_denoms = [ULUNA]
                    options.gas_prices = {ULUNA: self.gas_list[ULUNA]}

                tx:Tx = None
                while True:
                    try:
                        tx:Tx = self.current_wallet.create_and_sign_tx(options)
                        break
                    except LCDResponseError as err:
                        # if 'account sequence mismatch' in err.message:
                        #     self.sequence    = self.sequence + 1
                        #     options.sequence = self.sequence
                        #     print (' 🛎️  Boosting sequence number')
                        # else:
                        print (err)
                        break
                    except Exception as err:
                        
                        print (' 🛑 A random error has occurred')
                        print (err)
                        break

                self.transaction = tx

                return True
            else:
                return False
        else:
            print ('No belief price calculated - did you run the simulation first?')
            return False
  
    def swapRate(self) -> float:
        """
        Get the swap rate based on the provided details.
        Returns a float value of the amount
        """
        
        estimated_amount:float = None

        if self.use_market_swap == False:

            if self.swap_denom == UBASE:
                if self.swap_request_denom == ULUNA:
                    swap_price = self.beliefPrice()
                    estimated_amount = float(self.swap_amount * swap_price)
                
            else:
                # This will cover nearly all swap pairs:
                swap_price = self.beliefPrice()
                if swap_price is not None and swap_price > 0:
                    estimated_amount = float(self.swap_amount / swap_price)
                    
        else:
            off_chain_coins = [ULUNA, UOSMO, UATOM, UKUJI, WETH]
            if self.swap_denom in off_chain_coins and self.swap_request_denom in off_chain_coins:
                # Calculate the amount of OSMO we'll be getting:
                # (lunc amount * lunc unit cost) / osmo price
                prices:json = self.getPrices(self.swap_denom, self.swap_request_denom)
                estimated_amount:float = (self.swap_amount * float(prices['from']) / float(prices['to']))

        return estimated_amount
    
class WithdrawalTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(WithdrawalTransaction, self).__init__(*args, **kwargs)

        self.delegator_address:str = ''
        self.validator_address:str = ''

    def create(self, delegator_address:str, validator_address:str):
        """
        Create a withdrawal object and set it up with the provided details.
        """

        # Create the terra instance
        self.terra = TerraInstance().create()
        
        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()
        self.tax_rate = self.taxRate()

        # Store the delegator and validator addresses
        self.delegator_address:str = delegator_address
        self.validator_address:str = validator_address

        return self
    
    def simulate(self) -> bool:
        """
        Simulate a withdrawal so we can get the fee details.
        The fee details are saved so the actual withdrawal will work.
        """

        # Set the fee to be None so it is simulated
        self.fee      = None
        self.sequence = self.current_wallet.sequence()
        self.withdraw()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            self.fee = self.calculateFee(requested_fee)

            return True
        else:
            return False
        

    def withdraw(self) -> bool:
        """
        Make a withdrawal with the information we have so far.
        If fee is None then it will be a simulation.
        """

        try:
            tx:Tx = None

            msg = MsgWithdrawDelegatorReward(
                delegator_address = self.delegator_address,
                validator_address = self.validator_address
            )
            
            options = CreateTxOptions(
                fee        = self.fee,
                gas        = 'auto',
                gas_prices = self.gas_list,
                msgs       = [msg]
            )

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    if 'account sequence mismatch' in err.message:
                        self.sequence    = self.sequence + 1
                        options.sequence = self.sequence
                        print (' 🛎️  Boosting sequence number')
                    else:
                        print ('withdraw error:')
                        print (err)
                        break
                except Exception as err:
                    print (' 🛑 A random error has occurred')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        except:
            return False