#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import cryptocode
import json
import math
import requests
import time
import yaml

from utility_constants import (
    ASTROPORT_UUSD_TO_ULUNA_ADDRESS,
    COIN_DIVISOR,
    CONFIG_FILE_NAME,
    FULL_COIN_LOOKUP,
    GAS_ADJUSTMENT,
    GAS_ADJUSTMENT_SWAPS,
    GAS_PRICE_URI,
    LCD_ENDPOINT,
    SEARCH_RETRY_COUNT,
    TAX_RATE_URI,
    TERRASWAP_ULUNA_TO_UUSD_ADDRESS,
    #TERRASWAP_UUSD_TO_ULUNA_ADDRESS,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
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
    
def get_coin_selection(question:str, coins:dict, only_active_coins:bool = True, estimation_against:dict = None, wallet:Wallet = False) -> str | str | float:
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
    coin_list = []
    coin_values = {}
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
                swaps_tx.swap_amount = int(estimation_against['amount'])
                swaps_tx.swap_denom =  estimation_against['denom']

                swaps_tx.swap_request_denom = coin

                if coin != estimation_against['denom']:
                    estimated_result:Coin = swaps_tx.swapRate()
                    estimated_value:str = wallet.formatUluna(estimated_result.amount)
                else:
                    estimated_result:Coin = Coin(estimation_against['denom'], 1 * COIN_DIVISOR)
                    estimated_value = None
                
                coin_values[coin] = estimated_value
                
                if len(str(estimated_value)) > label_widths[3]:
                    label_widths[3] = len(str(estimated_value))

    padding_str = ' ' * 100

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

    coin_to_use:str = None
    returned_estimation: float = None    
    answer:str = False

    coin_index = {}
    while True:

        count:int = 0

        print ('\n' + horizontal_spacer)
        print (header_string)
        print (horizontal_spacer)

        for coin in FULL_COIN_LOOKUP:

            if coin in coins:
                count += 1
                coin_index[FULL_COIN_LOOKUP[coin].lower()] = count
            else:
                print (f'{coin} not in coins')
            
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
                coin_val = ''
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
                coin_to_use = coin_list[int(answer)]
                if estimation_against is not None:
                    returned_estimation = coin_values[coin_to_use]
                
        if answer == USER_ACTION_CONTINUE:
            if coin_to_use is not None:
                break
            else:
                print ('\nPlease select a coin first.\n')

        if answer == USER_ACTION_QUIT:
            break

    return coin_to_use, answer, returned_estimation
    
def get_user_choice(question:str, allowed_options:list) -> str|bool:
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

def get_user_number(question:str, params:dict) -> float|str:
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

    #log:str = 'insufficient fees; got: "93930uidr,4811427uluna", required: "179439uaud,179439ucad,132219uchf,925527ucny,849974udkk,118052ueur,103886ugbp,1104966uhkd,2058918253uidr,10275236uinr,15460074ujpy,160550550ukrw,5350111uluna,404748881umnt,566649umyr,1180519unok,7177554uphp,99106usdr,1180519usek,188883usgd,4363198uthb,3777660utwd,141663uusd" = "179439uaud,179439ucad,132219uchf,925527ucny,849974udkk,118052ueur,103886ugbp,1104966uhkd,2058824700uidr,10275236uinr,15460074ujpy,160550550ukrw,5350111uluna,404748881umnt,566649umyr,1180519unok,7177554uphp,99106usdr,1180519usek,188883usgd,4363198uthb,3777660utwd,141663uusd"(gas) +"93553uidr"(stability): insufficient fee'
    required = log.split('required:')

    parts = required[1].split('=')

    fee_line = parts[1]
    fee_line = fee_line.replace('(stability): insufficient fee', '').replace('"', '').lstrip(' ') .split('(gas) +')

    fee_coins = Coins.from_str(fee_line[0])
    result_tax_coin = Coin.from_str(fee_line[1])

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
        self.file         = None
        self.wallets:dict = {}

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

        return self
        
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

        self.terra = TerraInstance().create()

        return self
    
    def delegate(self):
        """
        Update the delegate class with the data it needs
        It will be created via the create() command
        """

        self.delegateTx.seed     = self.seed
        self.delegateTx.balances = self.balances

        return self.delegateTx

    def formatUluna(self, uluna:float, add_suffix:bool = False) -> float|str:
        """
        A generic helper function to convert uluna amounts to LUNC.
        """

        lunc:float = round(float(uluna / COIN_DIVISOR), 6)

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
                pagOpt.key          = pagination["next_key"]
                result, pagination  = self.terra.bank.balance(address = self.address, params = pagOpt)
                for coin in result:
                    balances[coin.denom] = coin.amount

            self.balances = balances

        return self.balances
    
    def getDelegations(self):
        """
        Get the delegations associated with this wallet address.
        The results are cached so if the list is refreshed then it is much quicker.
        """

        if self.delegation_details is None:
            self.delegation_details = Delegations().create(self.address)

        return self.delegation_details
    
    def getUndelegations(self):
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
        mk = MnemonicKey()
        
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
    
    def validateAddress(self, address:str) -> bool | bool:
        """
        Check that the provided address actually resolves to a terra wallet.
        """

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
        self.chain_id       = 'columbus-5'
        self.gas_adjustment = float(GAS_ADJUSTMENT)
        #self.gas_list       = None
        #self.gas_price_url  = gas_price_url
        #self.tax_rate      = None
        self.terra          = None
        self.url            = LCD_ENDPOINT
        
    def create(self) -> LCDClient:
        """
        Create an LCD client instance and store it in this object.
        """

        terra:LCDClient = LCDClient(
            chain_id        = self.chain_id,
            gas_adjustment  = float(self.gas_adjustment),
            url             = self.url
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
        terra              = TerraInstance()
        self.terra         = terra.create()

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

        other_coin_list:list = []
        has_uluna:int        = 0
        has_uusd:int         = 0
        
        coin:Coin

        #print (requested_fee)
        #print (self.balances)

        for coin in requested_fee.amount:
            if coin.denom in self.balances and self.balances[coin.denom] >= coin.amount:

                #print (f"{coin.denom} = {self.balances[coin.denom]}, amount={coin.amount}")
                if coin.denom == 'uusd':
                    has_uusd = coin.amount
                elif coin.denom == 'uluna':
                    has_uluna = coin.amount
                else:
                    other_coin_list.append(coin)

                if coin.denom == specific_denom:
                    specific_denom_amount = coin.amount

        #print (other_coin_list)

        if has_uluna > 0 or has_uusd > 0 or len(other_coin_list) > 0:
            
            # @TODO: check that this works for random alts
            if len(other_coin_list) > 0:
                requested_fee.amount = Coins({Coin(other_coin_list[0].denom, other_coin_list[0].amount)})
            elif has_uluna > 0:
                requested_fee.amount = Coins({Coin('uluna', has_uluna)})
            else:
                requested_fee.amount = Coins({Coin('uusd', has_uusd)})

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
                    #print (result)
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
                amount            = Coin('uluna', self.delegated_uluna)
            )

            options = CreateTxOptions(
                fee        = self.fee,
                #fee_denoms  = ['uluna', 'uusd', 'uaud' ,'ukrw'], # 
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
                    #BlockTxBroadcastResult(height=0, txhash='xxx', raw_log='account sequence mismatch, expected 336, got 335: incorrect account sequence', gas_wanted=540431, gas_used=41957, logs=None, code=32, codespace='sdk', info=None, data=None, timestamp=None)
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
                amount                = Coin('uluna', self.delegated_uluna)
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
                amount            = Coin('uluna', int(self.delegated_uluna))
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
        self.memo:str              = ''
        self.recipient_address:str = ''
        self.sequence:int          = None
        self.tax:float             = None

    def create(self):
        """
        Create a send object and set it up with the provided details.
        """

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

        #print ('send amount before:', send_amount)
        #print ('tax:', self.tax)
        #print ('fee deductiables:', self.fee_deductables)
        #print ('balance available:', self.balances[self.denom])
        if self.tax is not None:
            if self.fee_deductables is not None:
                if send_amount + self.tax > self.balances[self.denom]:
        #            print ('send amount + tax exceeds total amount available')
                    
                    send_amount = int(send_amount - self.fee_deductables)
            
        #print ('send_amount after:', send_amount)

        try:
            tx:Tx = None

            msg = MsgSend(
                from_address = self.current_wallet.key.acc_address,
                to_address   = self.recipient_address,
                amount       = Coins(str(int(send_amount)) + self.denom)
            )

            #print ('GAS LIMIT:', self.gas_limit)

            options = CreateTxOptions(
                fee        = self.fee,
                gas        = str(self.gas_limit),
                #gas = str(200000),
                gas_prices = self.gas_list,
                memo       = self.memo,
                msgs       = [msg],
                sequence   = self.sequence,
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
            self.sequence        = self.current_wallet.sequence()
        
        # Perform the swap as a simulation, with no fee details
        self.send()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            #print ('requested fee:', requested_fee)

            # Store the gas limit based on what we've been told
            self.gas_limit = requested_fee.gas_limit

            #print ('apparent gas requirement:', self.gas_limit)

            #self.gas_limit = str(int(requested_fee.gas_limit) * 1.3).rstrip('.0')
            #print ('apparent gas requirement:', self.gas_limit)
            #self.send()

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple
            self.fee = self.calculateFee(requested_fee, 'uluna')
            
            #print ('calculated fee:', self.fee)
            
            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
            fee_denom    = fee_bit.denom

            # Calculate the tax portion
            self.tax = int(math.ceil(self.amount * float(self.tax_rate['tax_rate'])))

            #print ('tax is', self.tax)
            #print ('fee denom:', fee_denom)
            #print ('self denom:', self.denom)

            # Build a fee object
            if fee_denom == 'uluna' and self.denom == 'uluna':
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
            else:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount)), Coin(self.denom, int(self.tax))})
                
            #if self.gas_limit != 'auto':
            #   requested_fee.gas_limit = int(self.gas_limit)

            requested_fee.amount = new_coin

            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            # Store this so we can deduct it off the total amount to swap.
            # If the fee denom is the same as what we're paying the tax in, then combine the two
            # Otherwise the deductible is just the tax value
            # This assumes that the tax is always the same denom as the transferred amount.
            if fee_denom == self.denom:
                self.fee_deductables = int(fee_amount + self.tax)
            elif fee_denom == 'uluna' and self.denom == 'uusd':
                self.fee_deductables = int(self.tax)
            else:
                self.fee_deductables = int(self.tax * 2)

            #print ('FINAL requested fee:', requested_fee)
            #print ('fee deductables:', self.fee_deductables)

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

    def beliefPrice(self) -> float:
        """
        Figure out the belief price for this swap.
        """

        result = self.terra.wasm.contract_query(self.contract, {"pool": {}})

        parts:dict = {}
        parts[result['assets'][0]['info']['native_token']['denom']] = int(result['assets'][0]['amount'])
        parts[result['assets'][1]['info']['native_token']['denom']] = int(result['assets'][1]['amount'])

        belief_price:float = parts['uluna'] / parts['uusd']
        return round(belief_price, 18)
        
    def create(self):
        """
        Create a swap object and set it up with the provided details.
        """

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

        #self.belief_price    = None
        #self.fee             = None
        #self.tax             = None
        #self.fee_deductables = None
        self.sequence        = self.current_wallet.sequence()

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

        # Send:
#         ,terra1adfylse87rxmuh95592n99zdne4rudzwxucl35,terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552{"swap":{"belief_price":"0.005405309185445239","max_spread":"0.01","offer_asset":{"amount":"21634971","info":{"native_token":{"denom":"uusd"}}}}}*
# uusd216349
        # Result:
        # {
        #     "gas_info": {
        #         "gas_wanted": "0",
        #         "gas_used": "241592"
        #     },
        #     "result": {
        #         "data": "CigKJi90ZXJyYS53YXNtLnYxYmV0YTEuTXNnRXhlY3V0ZUNvbnRyYWN0",
        #         "log": "[{\"events\":[{\"type\":\"coin_received\",\"attributes\":[{\"key\":\"receiver\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"21634971uusd\"},{\"key\":\"receiver\",\"value\":\"terra17xpfvakm2amg962yls6f84z3kell8c5lkaeqfa\"},{\"key\":\"amount\",\"value\":\"7989103uluna\"},{\"key\":\"receiver\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"amount\",\"value\":\"3994551779uluna\"},{\"key\":\"receiver\",\"value\":\"terra17xpfvakm2amg962yls6f84z3kell8c5lkaeqfa\"},{\"key\":\"amount\",\"value\":\"8012uluna\"},{\"key\":\"receiver\",\"value\":\"terra12u7hcmpltazmmnq0fvyl225usn3fy6qqlp05w0\"},{\"key\":\"amount\",\"value\":\"4006169uluna\"}]},{\"type\":\"coin_spent\",\"attributes\":[{\"key\":\"spender\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"amount\",\"value\":\"21634971uusd\"},{\"key\":\"spender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"7989103uluna\"},{\"key\":\"spender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"3994551779uluna\"},{\"key\":\"spender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"8012uluna\"},{\"key\":\"spender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"4006169uluna\"}]},{\"type\":\"execute_contract\",\"attributes\":[{\"key\":\"sender\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"contract_address\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"}]},{\"type\":\"from_contract\",\"attributes\":[{\"key\":\"contract_address\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"action\",\"value\":\"swap\"},{\"key\":\"sender\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"receiver\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"offer_asset\",\"value\":\"uusd\"},{\"key\":\"ask_asset\",\"value\":\"uluna\"},{\"key\":\"offer_amount\",\"value\":\"21634971\"},{\"key\":\"return_amount\",\"value\":\"4002540883\"},{\"key\":\"tax_amount\",\"value\":\"7989104\"},{\"key\":\"spread_amount\",\"value\":\"11850\"},{\"key\":\"commission_amount\",\"value\":\"12043753\"},{\"key\":\"maker_fee_amount\",\"value\":\"4014182\"}]},{\"type\":\"message\",\"attributes\":[{\"key\":\"action\",\"value\":\"/terra.wasm.v1beta1.MsgExecuteContract\"},{\"key\":\"module\",\"value\":\"wasm\"},{\"key\":\"sender\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"sender\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"sender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"sender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"module\",\"value\":\"bank\"},{\"key\":\"sender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"sender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"module\",\"value\":\"bank\"}]},{\"type\":\"transfer\",\"attributes\":[{\"key\":\"recipient\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"sender\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"amount\",\"value\":\"21634971uusd\"},{\"key\":\"recipient\",\"value\":\"terra17xpfvakm2amg962yls6f84z3kell8c5lkaeqfa\"},{\"key\":\"sender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"7989103uluna\"},{\"key\":\"recipient\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"sender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"3994551779uluna\"},{\"key\":\"recipient\",\"value\":\"terra17xpfvakm2amg962yls6f84z3kell8c5lkaeqfa\"},{\"key\":\"sender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"8012uluna\"},{\"key\":\"recipient\",\"value\":\"terra12u7hcmpltazmmnq0fvyl225usn3fy6qqlp05w0\"},{\"key\":\"sender\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"amount\",\"value\":\"4006169uluna\"}]},{\"type\":\"wasm\",\"attributes\":[{\"key\":\"contract_address\",\"value\":\"terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552\"},{\"key\":\"action\",\"value\":\"swap\"},{\"key\":\"sender\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"receiver\",\"value\":\"terra1adfylse87rxmuh95592n99zdne4rudzwxucl35\"},{\"key\":\"offer_asset\",\"value\":\"uusd\"},{\"key\":\"ask_asset\",\"value\":\"uluna\"},{\"key\":\"offer_amount\",\"value\":\"21634971\"},{\"key\":\"return_amount\",\"value\":\"4002540883\"},{\"key\":\"tax_amount\",\"value\":\"7989104\"},{\"key\":\"spread_amount\",\"value\":\"11850\"},{\"key\":\"commission_amount\",\"value\":\"12043753\"},{\"key\":\"maker_fee_amount\",\"value\":\"4014182\"}]}]}]",
        #         "events": [
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "YWN0aW9u",
        #                 "value": "L3RlcnJhLndhc20udjFiZXRhMS5Nc2dFeGVjdXRlQ29udHJhY3Q=",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "execute_contract",
        #             "attributes": [
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "Y29udHJhY3RfYWRkcmVzcw==",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "bW9kdWxl",
        #                 "value": "d2FzbQ==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_spent",
        #             "attributes": [
        #             {
        #                 "key": "c3BlbmRlcg==",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "MjE2MzQ5NzF1dXNk",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_received",
        #             "attributes": [
        #             {
        #                 "key": "cmVjZWl2ZXI=",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "MjE2MzQ5NzF1dXNk",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "transfer",
        #             "attributes": [
        #             {
        #                 "key": "cmVjaXBpZW50",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "MjE2MzQ5NzF1dXNk",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "wasm",
        #             "attributes": [
        #             {
        #                 "key": "Y29udHJhY3RfYWRkcmVzcw==",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YWN0aW9u",
        #                 "value": "c3dhcA==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "cmVjZWl2ZXI=",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "b2ZmZXJfYXNzZXQ=",
        #                 "value": "dXVzZA==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YXNrX2Fzc2V0",
        #                 "value": "dWx1bmE=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "b2ZmZXJfYW1vdW50",
        #                 "value": "MjE2MzQ5NzE=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "cmV0dXJuX2Ftb3VudA==",
        #                 "value": "NDAwMjU0MDg4Mw==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "dGF4X2Ftb3VudA==",
        #                 "value": "Nzk4OTEwNA==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c3ByZWFkX2Ftb3VudA==",
        #                 "value": "MTE4NTA=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "Y29tbWlzc2lvbl9hbW91bnQ=",
        #                 "value": "MTIwNDM3NTM=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "bWFrZXJfZmVlX2Ftb3VudA==",
        #                 "value": "NDAxNDE4Mg==",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "from_contract",
        #             "attributes": [
        #             {
        #                 "key": "Y29udHJhY3RfYWRkcmVzcw==",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YWN0aW9u",
        #                 "value": "c3dhcA==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "cmVjZWl2ZXI=",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "b2ZmZXJfYXNzZXQ=",
        #                 "value": "dXVzZA==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YXNrX2Fzc2V0",
        #                 "value": "dWx1bmE=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "b2ZmZXJfYW1vdW50",
        #                 "value": "MjE2MzQ5NzE=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "cmV0dXJuX2Ftb3VudA==",
        #                 "value": "NDAwMjU0MDg4Mw==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "dGF4X2Ftb3VudA==",
        #                 "value": "Nzk4OTEwNA==",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c3ByZWFkX2Ftb3VudA==",
        #                 "value": "MTE4NTA=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "Y29tbWlzc2lvbl9hbW91bnQ=",
        #                 "value": "MTIwNDM3NTM=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "bWFrZXJfZmVlX2Ftb3VudA==",
        #                 "value": "NDAxNDE4Mg==",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_spent",
        #             "attributes": [
        #             {
        #                 "key": "c3BlbmRlcg==",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "Nzk4OTEwM3VsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_received",
        #             "attributes": [
        #             {
        #                 "key": "cmVjZWl2ZXI=",
        #                 "value": "dGVycmExN3hwZnZha20yYW1nOTYyeWxzNmY4NHoza2VsbDhjNWxrYWVxZmE=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "Nzk4OTEwM3VsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "transfer",
        #             "attributes": [
        #             {
        #                 "key": "cmVjaXBpZW50",
        #                 "value": "dGVycmExN3hwZnZha20yYW1nOTYyeWxzNmY4NHoza2VsbDhjNWxrYWVxZmE=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "Nzk4OTEwM3VsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_spent",
        #             "attributes": [
        #             {
        #                 "key": "c3BlbmRlcg==",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "Mzk5NDU1MTc3OXVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_received",
        #             "attributes": [
        #             {
        #                 "key": "cmVjZWl2ZXI=",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "Mzk5NDU1MTc3OXVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "transfer",
        #             "attributes": [
        #             {
        #                 "key": "cmVjaXBpZW50",
        #                 "value": "dGVycmExYWRmeWxzZTg3cnhtdWg5NTU5Mm45OXpkbmU0cnVkend4dWNsMzU=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "Mzk5NDU1MTc3OXVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "bW9kdWxl",
        #                 "value": "YmFuaw==",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_spent",
        #             "attributes": [
        #             {
        #                 "key": "c3BlbmRlcg==",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "ODAxMnVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_received",
        #             "attributes": [
        #             {
        #                 "key": "cmVjZWl2ZXI=",
        #                 "value": "dGVycmExN3hwZnZha20yYW1nOTYyeWxzNmY4NHoza2VsbDhjNWxrYWVxZmE=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "ODAxMnVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "transfer",
        #             "attributes": [
        #             {
        #                 "key": "cmVjaXBpZW50",
        #                 "value": "dGVycmExN3hwZnZha20yYW1nOTYyeWxzNmY4NHoza2VsbDhjNWxrYWVxZmE=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "ODAxMnVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_spent",
        #             "attributes": [
        #             {
        #                 "key": "c3BlbmRlcg==",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "NDAwNjE2OXVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "coin_received",
        #             "attributes": [
        #             {
        #                 "key": "cmVjZWl2ZXI=",
        #                 "value": "dGVycmExMnU3aGNtcGx0YXptbW5xMGZ2eWwyMjV1c24zZnk2cXFscDA1dzA=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "NDAwNjE2OXVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "transfer",
        #             "attributes": [
        #             {
        #                 "key": "cmVjaXBpZW50",
        #                 "value": "dGVycmExMnU3aGNtcGx0YXptbW5xMGZ2eWwyMjV1c24zZnk2cXFscDA1dzA=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             },
        #             {
        #                 "key": "YW1vdW50",
        #                 "value": "NDAwNjE2OXVsdW5h",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "c2VuZGVy",
        #                 "value": "dGVycmExbTZ5d2xnbjZ3cmp1YWdjbW1lenp6MmEwMjlndGxkaGV5NWs1NTI=",
        #                 "index": false
        #             }
        #             ]
        #         },
        #         {
        #             "type": "message",
        #             "attributes": [
        #             {
        #                 "key": "bW9kdWxl",
        #                 "value": "YmFuaw==",
        #                 "index": false
        #             }
        #             ]
        #         }
        #         ]
        #     }
        # }
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

            #print ('requested fee:', requested_fee)

            # Store the gas limit based on what we've been told
            #self.gas_limit = str(requested_fee.gas_limit)

            #print ('apparent gas requirement:', self.gas_limit)

            #self.gas_limit = str(int(requested_fee.gas_limit) * 1.3).rstrip('.0')
            #print ('apparent gas requirement:', self.gas_limit)
            #self.send()

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple
            self.fee = self.calculateFee(requested_fee, 'uluna')
            
            #print ('calculated fee:', self.fee)
            
            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
            fee_denom    = fee_bit.denom

            # Calculate the tax portion
            self.tax = int(math.ceil(self.swap_amount * float(self.tax_rate['tax_rate'])))

            #print ('tax is', self.tax)
            #print ('fee denom:', fee_denom)
            #print ('self denom:', self.denom)

            # Build a fee object
            if fee_denom == 'uluna' and self.swap_denom == 'uluna':
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount + self.tax))})
            else:
                new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount)), Coin(self.swap_denom, int(self.tax))})
                
            #if self.gas_limit != 'auto':
            #   requested_fee.gas_limit = int(self.gas_limit)

            requested_fee.amount = new_coin

            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            # Store this so we can deduct it off the total amount to swap.
            # If the fee denom is the same as what we're paying the tax in, then combine the two
            # Otherwise the deductible is just the tax value
            # This assumes that the tax is always the same denom as the transferred amount.
            if fee_denom == self.swap_denom:
                self.fee_deductables = int(fee_amount + self.tax)
            elif fee_denom == 'uluna' and self.swap_denom == 'uusd':
                self.fee_deductables = int(self.tax)
            else:
                self.fee_deductables = int(self.tax * 2)

            print ('FINAL requested fee:', requested_fee)
            print ('fee deductables:', self.fee_deductables)

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
                fee_denom:str   = 'uusd'

            if fee_denom in self.balances:
                #print ('self.swap_amount:', self.swap_amount)
                swap_amount = self.swap_amount

                #if self.tax is not None:
                #    if self.fee_deductables is not None:
                #        print ('fee deductables:', self.fee_deductables)
                #        swap_amount = swap_amount - self.fee_deductables

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
                    #gas        = str(self.gas_limit),
                    gas_prices = self.gas_list,
                    msgs       = [tx_msg],
                    sequence   = self.sequence,
                )

                print ('options:', options)
                # If we are swapping from lunc to usdt then we need a different fee structure
                if self.swap_denom == 'uluna' and self.swap_request_denom == 'uusd':
                    options.fee_denoms = ['uluna']
                    options.gas_prices = {'uluna': self.gas_list['uluna']}

                tx:Tx = None
                while True:
                    try:
                        tx:Tx = self.current_wallet.create_and_sign_tx(options)

                        print ('tx:', tx)
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

        if self.swap_denom == 'uusd' and self.swap_request_denom == 'uluna':
            self.contract = ASTROPORT_UUSD_TO_ULUNA_ADDRESS
            #self.contract = TERRASWAP_UUSD_TO_ULUNA_ADDRESS
            swap_price = self.beliefPrice()
            swap_details:Coin = Coin(self.swap_request_denom, int(self.swap_amount * swap_price))
        elif self.swap_denom == 'uluna' and self.swap_request_denom == 'uusd':
            self.contract = TERRASWAP_ULUNA_TO_UUSD_ADDRESS
            swap_price = self.beliefPrice()
            swap_details:Coin = Coin(self.swap_request_denom, int(self.swap_amount * swap_price))
        else:
        #print (self.swap_denom, ' vs ', self.swap_request_denom)
            swap_details:Coin = self.terra.market.swap_rate(Coin(self.swap_denom, self.swap_amount), self.swap_request_denom)
        #print (swap_details)

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

        self.delegator_address:str = delegator_address
        self.validator_address:str = validator_address
        
        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()
        self.tax_rate = self.taxRate()

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