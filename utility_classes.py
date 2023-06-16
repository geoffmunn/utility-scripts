#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import cryptocode
import json
import math
import requests
import time
import yaml

import traceback

from utility_constants import (
    ASTROPORT_UUSD_TO_UKUJI_ADDRESS,
    ASTROPORT_UUSD_TO_ULUNA_ADDRESS,
    CHAIN_IDS,
    COIN_DIVISOR,
    CONFIG_FILE_NAME,
    FULL_COIN_LOOKUP,
    GAS_ADJUSTMENT,
    GAS_ADJUSTMENT_SWAPS,
    GAS_PRICE_URI,
    UKUJI,
    KUJI_SMART_CONTACT_ADDRESS,
    SEARCH_RETRY_COUNT,
    TAX_RATE_URI,
    #TERRASWAP_UKUJI_TO_ULUNA_ADDRESS,
    TERRASWAP_UKRW_TO_ULUNA_ADDRESS,
    TERRASWAP_ULUNA_TO_UUSD_ADDRESS,
    ULUNA,
    UKRW,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
    UUSD,
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

def coin_list(input: Coins, existingList: dict) -> dict:
    """ 
    Converts the Coins list into a dictionary.
    There might be a built-in function for this, but I couldn't get it working.
    """

    coin:Coin
    for coin in input:
        existingList[coin.denom] = coin.amount

    return existingList

def isDigit(value):
    """
    A better method for identifying digits. This one can handle decimal places.
    """

    try:
        float(value)
        return True
    except ValueError:
        return False
    
def isPercentage(value:str):
    """
    A helpter function to figure out if a value is a percentage or not.
    """
    last_char = str(value).strip(' ')[-1]
    if last_char == '%':
        return True
    else:
        return False
    
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
                coin_val = wallet.formatUluna(coins[coin])

                if len(str(coin_val)) > label_widths[2]:
                    label_widths[2] = len(str(coin_val))

            if estimation_against is not None:

                # Set up the swap details
                swaps_tx.swap_amount        = int(estimation_against['amount'])
                swaps_tx.swap_denom         = estimation_against['denom']
                swaps_tx.swap_request_denom = coin

                # Change the contract depending on what we're doing
                swaps_tx.setContract()

                if coin != estimation_against['denom']:
                    estimated_result:Coin = swaps_tx.swapRate()
                    estimated_value:str   = wallet.formatUluna(estimated_result.amount)

                    if estimated_value == '0':
                        estimated_value = None
                else:
                    estimated_result:Coin = Coin(estimation_against['denom'], 1 * COIN_DIVISOR)
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
    returned_estimation: float = None    
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
                coin_val = wallet.formatUluna(coins[coin])

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
                            estimated_str = float(coin_values[coin])
                            estimated_str = str(("%.6f" % (estimated_str)).rstrip('0').rstrip('.'))
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

    if answer != '':
        if 'percentages_allowed' in params and is_percentage == True:
            if 'convert_percentages' in params and params['convert_percentages'] == True:
                wallet:Wallet = Wallet()
                answer = float(wallet.convertPercentage(answer, params['keep_minimum'], params['max_number']))
            else:
                answer = answer + '%'
        else:
            if convert_to_uluna == True:
                answer = float(float(answer) * COIN_DIVISOR)

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

        if 'delegations' in wallet:
            if 'redelegate' in wallet['delegations']:
                delegation_amount = wallet['delegations']['redelegate']
                if 'threshold' in wallet['delegations']:
                    threshold = wallet['delegations']['threshold']

        wallet_item:Wallet = Wallet().create(wallet['wallet'], wallet['address'], wallet['seed'], user_password)
        wallet_item.updateDelegation(delegation_amount, threshold)

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

                if 'delegations' in wallet:
                    if 'redelegate' in wallet['delegations']:
                        delegation_amount = wallet['delegations']['redelegate']
                        if 'threshold' in wallet['delegations']:
                            threshold = wallet['delegations']['threshold']


                wallet_item:Wallet = Wallet().create(wallet['wallet'], wallet['address'], wallet['seed'], user_password)
                wallet_item.updateDelegation(delegation_amount, threshold)

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
        self.allow_swaps:bool          = True
        self.balances:dict             = None
        self.delegateTx                = DelegationTransaction()
        self.delegation_details:dict   = None
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
    
    def convertPercentage(self, percentage:float, keep_minimum:bool, target_amount:float):
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
        uluna_amount:int  = int(lunc_amount * COIN_DIVISOR)
        
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

    def formatUluna(self, uluna:float, add_suffix:bool = False):
        """
        A generic helper function to convert uluna amounts to LUNC.
        """

        lunc:float = round(float(int(uluna) / COIN_DIVISOR), 6)

        lunc = ("%.6f" % (lunc)).rstrip('0').rstrip('.')

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
            result:Coins
            result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)

            # Convert the result into a friendly list
            balances:dict = {}
            for coin in result:
                balances[coin.denom] = coin.amount

            # Go through the pagination (if any)
            while pagination['next_key'] is not None:
                pagOpt.key         = pagination["next_key"]
                result, pagination = self.terra.bank.balance(address = self.address, params = pagOpt)
                for coin in result:
                    balances[coin.denom] = coin.amount

            # Add the extra coins (Kuji etc)
            #coin_balance = self.terra.wasm.contract_query(KUJI_SMART_CONTACT_ADDRESS, {'balance':{'address':self.address}})
            #if int(coin_balance['balance']) > 0:
            #    balances[UKUJI] = coin_balance['balance']

            self.balances = balances

        return self.balances
    
    def getDelegations(self) -> dict:
        """
        Get the delegations associated with this wallet address.
        The results are cached so if the list is refreshed then it is much quicker.
        """

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
            self.undelegation_details = Undelegations().create(self.address)

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
            generated_wallet_key     = MnemonicKey(self.seed)
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
        #self.chain_id       = DEFAULT_CHAIN_ID
        self.gas_adjustment = float(GAS_ADJUSTMENT)
        self.terra          = None
        #self.url            = LCD_ENDPOINT
        
    def create(self, prefix:str = 'terra') -> LCDClient:
        """
        Create an LCD client instance and store it in this object.
        """

        if prefix in CHAIN_IDS:
            self.chain_id = CHAIN_IDS[prefix]['chain_id']
            self.url      = CHAIN_IDS[prefix]['lcd_urls'][0]

            terra:LCDClient = LCDClient(
                chain_id       = self.chain_id,
                gas_adjustment = float(self.gas_adjustment),
                url            = self.url
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
        self.delegations[validator_name] = {'balance_amount': balance_amount, 'balance_denom': balance_denom, 'commission': validator_commission, 'delegator': delegator_address, 'rewards': reward_coins, 'validator': validator_address,  'validator_name': validator_name}
        
    def create(self, wallet_address:str) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

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
        entries:list          = undelegation.entries

        # Get the total balance from all the entries
        balance_total:int = 0
        for entry in entries:
            balance_total += entry.balance

        # Set up the object with the details we're interested in
        self.undelegations[validator_address] = {'balance_amount': balance_total, 'delegator_address': delegator_address, 'validator_address': validator_address, 'entries': entries}
 
    def create(self, wallet_address:str) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

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
            
            current:dict = sorted_validators[moniker]

            current[moniker] = self.validators[validator]['voting_power']

            sorted_validators[moniker] = key


        sorted_list:list = sorted(sorted_validators.items(), key=lambda x:x[1], reverse=True)[0:130]
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
                # Wait for this transaction to appear in the blockchain
                if not self.broadcast_result.is_tx_error():
                    while True:
                        result:dict = self.terra.tx.search([("tx.hash", self.broadcast_result.txhash)])
                        self.terra.tx.search
                        
                        if len(result['txs']) > 0:
                            print ('Transaction received')
                            break
                            
                        else:
                            print ('No such tx yet...')

                # Find the transaction on the network and return the result
                try:
                    if 'code' in result and result.code == 5:
                        print (' 🛑 A transaction error occurred.')
            
                    else:
                        transaction_confirmed = self.findTransaction()

                        if transaction_confirmed == True:
                            print ('This transaction should be visible in your wallet now.')
                        else:
                            print ('The transaction did not appear after many searches. Future transactions might fail due to a lack of expected funds.')
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
            
            # @TODO: check that this works for random alts
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

        #print ('calculated fee:', requested_fee)
        return requested_fee

    def findTransaction(self) -> bool:
        """
        Do a search for any transaction with the current tx hash.
        If it can't be found within 10 attempts, then give up.
        """

        transaction_found:bool = False

        result:dict = self.terra.tx.search([
            ("message.sender", self.current_wallet.key.acc_address),
            ("message.recipient", self.current_wallet.key.acc_address),
            ('tx.hash', self.broadcast_result.txhash)
        ])

        retry_count = 0
        while True:
            if len(result['txs']) > 0 and int(result['pagination']['total']) > 0:
                if result['txs'][0].code == 0:
                    print ('Found the hash!')
                    transaction_found = True
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

                amount = fee_coin.amount / COIN_DIVISOR
                denom  = FULL_COIN_LOOKUP[fee_coin.denom]

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
        self.fee      = None
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

        self.amount:int            = 0
        self.denom:str             = ''
        self.fee:Fee               = None
        self.fee_deductables:float = None
        self.gas_limit:str         = 'auto'
        self.is_ibc_transfer:bool  = False
        self.memo:str              = ''
        self.recipient_address:str = ''
        self.sequence:int          = None
        self.source_channel:str    = None
        self.tax:float             = None

    def create(self):
        """
        Create a send object and set it up with the provided details.
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
                block_height:int = int(self.terra.tendermint.block_info()['block']['header']['height'])

                msg = MsgTransfer(
                    source_port       = 'transfer',
                    source_channel    = self.source_channel,
                    token             = Coin(self.denom, send_amount),
                    sender            = self.current_wallet.key.acc_address,
                    receiver          = self.recipient_address,
                    timeout_height    = Height(revision_number = 1, revision_height = block_height),                            
                    timeout_timestamp = 0
                )
                
                options = CreateTxOptions(
                    fee            = self.fee,
                    gas            = self.gas_limit,
                    gas_adjustment = 3,
                    gas_prices     = self.gas_list,
                    memo           = self.memo,
                    msgs           = [msg],
                    sequence       = self.sequence
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
                self.tax = int(math.ceil(self.amount * float(self.tax_rate['tax_rate'])))

                # Build a fee object
                if fee_denom == ULUNA and self.denom == ULUNA:
                    new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
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

        self.belief_price           = None
        self.contract               = None
        self.fee_deductables:float  = None
        self.gas_limit:str          = 'auto'
        self.max_spread:float       = 0.01
        self.tax:float              = None
        self.swap_amount:int        = None
        self.swap_denom:str         = None
        self.swap_request_denom:str = None
        self.use_market_swap:bool   = False

    def beliefPrice(self) -> float:
        """
        Figure out the belief price for this swap.
        """

        belief_price:float = 0

        if self.contract is not None:
            result = self.terra.wasm.contract_query(self.contract, {"pool": {}})
            
            parts:dict = {}
            if 'native_token' in result['assets'][0]['info']:
                parts[result['assets'][0]['info']['native_token']['denom']] = int(result['assets'][0]['amount'])
            else:
                if result['assets'][0]['info']['token']['contract_addr'] == KUJI_SMART_CONTACT_ADDRESS:
                    parts[UKUJI] = int(result['assets'][0]['amount'])

            parts[result['assets'][1]['info']['native_token']['denom']] = int(result['assets'][1]['amount'])

            contract_swaps:list  = [ULUNA, UKRW, UUSD, UKUJI]

            if self.swap_denom in contract_swaps and self.swap_request_denom in contract_swaps:

                if self.swap_denom == ULUNA:
                    if self.swap_request_denom == UUSD:
                        belief_price:float = parts[ULUNA] / parts[UUSD]
                    if self.swap_request_denom == UKRW:
                        belief_price:float = parts[ULUNA] / parts[UKRW]

                if self.swap_denom == UUSD:
                    if self.swap_request_denom == ULUNA:
                        belief_price:float = parts[UUSD] / parts[ULUNA]
                    if self.swap_request_denom == UKUJI:
                        belief_price:float = parts[UUSD] / parts[UKUJI]

                if self.swap_denom == UKRW:
                    if self.swap_request_denom == ULUNA:
                        belief_price:float = parts[UKRW] / parts[ULUNA]

                if self.swap_denom == UKUJI:
                    if self.swap_request_denom == UUSD:
                        belief_price:float = parts[UKUJI] / parts[UUSD]
                
        return round(belief_price, 18)
        
    def create(self):
        """
        Create a swap object and set it up with the provided details.
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
    
    def marketSimulate(self):
        """
        Simulate a market swap so we can get the fee details.
        The fee details are saved so the actual market swap will work.
        """

        self.sequence = self.current_wallet.sequence()

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
                trader = self.current_wallet.key.acc_address,
                offer_coin = Coin(self.swap_denom, self.swap_amount),
                ask_denom = self.swap_request_denom
            )

            options = CreateTxOptions(
                fee        = self.fee,
                gas        = self.gas_limit,
                gas_prices = self.gas_list,
                msgs       = [tx_msg],
                sequence   = self.sequence,
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

    def setContract(self) -> bool:
        """
        Depending on what the 'from' denom is and the 'to' denom, change the contract endpoint.

        If this is going to use a market swap, then we don't need a contract.
        """
        
        use_market_swap:bool = True
        self.contract        = None

        contract_swaps:list  = [ULUNA, UKRW, UUSD, UKUJI]

        if self.swap_denom in contract_swaps and self.swap_request_denom in contract_swaps:

            use_market_swap = False

            if self.swap_denom == ULUNA:
                if self.swap_request_denom == UUSD:
                    self.contract = TERRASWAP_ULUNA_TO_UUSD_ADDRESS
                if self.swap_request_denom == UKRW:
                    self.contract = TERRASWAP_UKRW_TO_ULUNA_ADDRESS

            if self.swap_denom == UUSD:
                if self.swap_request_denom == ULUNA:
                    self.contract = ASTROPORT_UUSD_TO_ULUNA_ADDRESS
                if self.swap_request_denom == UKRW:
                    self.contract = None
                    use_market_swap = True

            if self.swap_denom == UKRW:
                if self.swap_request_denom == ULUNA:
                    self.contract = TERRASWAP_UKRW_TO_ULUNA_ADDRESS
                if self.swap_request_denom == UUSD:
                    self.contract = None
                    use_market_swap = True

            if self.swap_denom == UUSD:
                if self.swap_request_denom == UKUJI:
                    self.contract = ASTROPORT_UUSD_TO_UKUJI_ADDRESS
            if self.swap_denom == UKUJI:
                if self.swap_request_denom == UUSD:
                    self.contract = ASTROPORT_UUSD_TO_UKUJI_ADDRESS

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

        self.belief_price = self.beliefPrice()
    
        if self.sequence is None:
            self.sequence = self.current_wallet.sequence()
        
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
            self.tax = int(math.ceil(self.swap_amount * float(self.tax_rate['tax_rate'])))

            # Build a fee object
            if fee_denom == ULUNA and self.swap_denom == ULUNA:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
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
            else:
                self.fee_deductables = int(self.tax * 2)

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
                        swap_amount = swap_amount - self.fee_deductables

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
                    fee        = self.fee,
                    gas_prices = self.gas_list,
                    msgs       = [tx_msg],
                    sequence   = self.sequence,
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

        
    def swapRate(self) -> Coin:
        """
        Get the swap rate based on the provided details.
        Returns a coin object that we need to decode.
        """

        if self.use_market_swap == False:
            if self.swap_denom == UUSD and self.swap_request_denom in [ULUNA, UKRW]:
                swap_price = self.beliefPrice()
                swap_details:Coin = Coin(self.swap_request_denom, int(self.swap_amount / swap_price))
            elif self.swap_denom == ULUNA and self.swap_request_denom in [UUSD, UKRW]:
                swap_price = self.beliefPrice()
                if self.swap_request_denom == UUSD:
                    swap_details:Coin = Coin(self.swap_request_denom, int(self.swap_amount / swap_price))
                else:
                    # ukrw
                    swap_details:Coin = Coin(self.swap_request_denom, int(self.swap_amount / swap_price))
            elif self.swap_denom == UKRW and self.swap_request_denom in [ULUNA, UUSD]:
                swap_price = self.beliefPrice()
                swap_details:Coin = Coin(self.swap_request_denom, int(self.swap_amount / swap_price))
            elif self.swap_denom == UUSD and self.swap_request_denom == UKUJI:
                swap_price = self.beliefPrice()
                swap_details:Coin = Coin(self.swap_request_denom, int(self.swap_amount / swap_price))
            elif self.swap_request_denom == UKUJI:
                swap_details:Coin = Coin(self.swap_request_denom, 0)
            elif self.swap_denom == UKUJI:
                if self.swap_request_denom == UUSD:
                    swap_price = self.beliefPrice()
                    swap_details:Coin = Coin(self.swap_request_denom, int(self.swap_amount / swap_price))
                else:
                    swap_details:Coin = Coin(self.swap_request_denom, 0)
            else:
                print ('UNSUPPORTED SWAP RATE')
                print ('swap denom:', self.swap_denom)
                print ('swap request denom:', self.swap_request_denom)
                exit()
        else:
            if self.swap_denom != UKUJI and self.swap_request_denom != UKUJI:
                swap_details:Coin = self.terra.market.swap_rate(Coin(self.swap_denom, self.swap_amount), self.swap_request_denom)
            else:
                swap_details:Coin = Coin(self.swap_request_denom, 0)

        return swap_details
    
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