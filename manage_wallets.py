#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml
import requests
import json
import cryptocode
import time

from getpass import getpass

from terra_sdk.client.lcd import LCDClient
from terra_sdk.client.lcd.api.distribution import Rewards
from terra_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
from terra_sdk.client.lcd.params import PaginationOptions
from terra_sdk.client.lcd.wallet import Wallet
from terra_sdk.core.bank import MsgSend
from terra_sdk.core.broadcast import BlockTxBroadcastResult
from terra_sdk.core.coin import Coin
from terra_sdk.core.coins import Coins
from terra_sdk.core.distribution.msgs import MsgWithdrawDelegatorReward
from terra_sdk.core.fee import Fee
from terra_sdk.core.staking import MsgDelegate
from terra_sdk.core.staking.data.delegation import Delegation
from terra_sdk.core.staking.data.validator import Validator
from terra_sdk.core.wasm.msgs import MsgExecuteContract
from terra_sdk.exceptions import LCDResponseError
from terra_sdk.key.mnemonic import MnemonicKey

# User settings - can be changed if required
WITHDRAWAL_REMAINDER = 100   # This is the amount of Lunc we want to keep after withdrawal and before delegating. You should never delegate the entire balance.

# System settings - these can be changed, but shouldn't be necessary
GAS_PRICE_URI       = 'https://fcd.terra.dev/v1/txs/gas_prices'
TAX_RATE_URI        = 'https://lcd.terra.dev/terra/treasury/v1beta1/tax_rate'
CONFIG_FILE_NAME    = 'user_config.yml'
GAS_ADJUSTMENT      = 3.5

# Do not change these
USER_ACTION_ALL               = 'a'
USER_ACTION_DELEGATE          = 'd'
USER_ACTION_SEND              = 't'
USER_ACTION_SWAP              = 's'
USER_ACTION_SWAP_DELEGATE     = 'sd'
USER_ACTION_WITHDRAW          = 'w'
USER_ACTION_WITHDRAW_DELEGATE = 'wd'

# Swap contracts can be found here
# https://assets.terra.money/cw20/pairs.dex.json
UUSD_TO_ULUNA_SWAP_ADDRESS      = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
ASTROPORT_UUSD_TO_ULUNA_ADDRESS = 'terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552'
ASTROPORT_UUSD_TO_MINA_ADDRESS = 'terra134m8n2epp0n40qr08qsvvrzycn2zq4zcpmue48'

def strtobool (val):
    """
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """

    val = val.lower()
    if val in ('y', 'yes', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'false', 'off', '0'):
        return False
    else:
        #raise ValueError("invalid truth value %r" % (val,))
        return -1
    
def get_user_choice(question:str, yes_choices:list, no_choices:list) -> str|bool:
    """
    Get the user selection for a prompt and convert it to a standard value.
    """

    while True:    
        answer = input(question).lower()
        if answer in yes_choices or answer in no_choices:
            break
    
    booly = strtobool(answer)
    if  booly== -1:
        result = answer
    else:
        result = booly

    return result

def get_user_multichoice(question:str, user_wallets:dict) -> dict|str:
    """
    Get multiple user selections from a list.
    This is a custom function because the options are specific to this list.
    """

    wallets_to_use = {}
    while True:

        count = 0
        wallet_numbers = {}

        for wallet_name in user_wallets:
            count += 1
            wallet_numbers[count] = user_wallets[wallet_name]
                
            if wallet_name in wallets_to_use:
                glyph = '✅'
            else:
                glyph = ''

            print (f"  ({count}) {glyph} {wallet_name}")
            
        answer = input(question).lower()
        
        if answer.isdigit() and int(answer) in wallet_numbers:
            key = wallet_numbers[int(answer)].name
            if key not in wallets_to_use:
                wallets_to_use[key] = wallet_numbers[int(answer)]
            else:
                wallets_to_use.pop(key)
            
        if answer == 'c':
            wallets_to_use = {}
        
        if answer == 'a':
            wallets_to_use = {}
            for wallet_name in user_wallets:
                wallets_to_use[wallet_name] = user_wallets[wallet_name]

        if answer == 'x':
            break

        if answer == 'q':
            break

    return wallets_to_use, answer

def coin_list(input: Coins, existingList: dict) -> dict:
    """ 
    Converts the Coins list into a dictionary.
    There might be a built-in function for this, but I couldn't get it working.
    """

    coin:Coin
    for coin in input:
        existingList[coin.denom] = coin.amount

    return existingList

class TerraInstance:
    def __init__(self, gas_price_url:str, gas_adjustment:float):
        self.chain_id       = 'columbus-5'
        self.gas_adjustment = gas_adjustment
        self.gas_price_url  = gas_price_url
        self.terra          = None
        #self.url            = 'https://lcd.terrarebels.net'
        #self.url            = 'https://lcd.terra.dev'
        self.url            =  'https://terra-classic-lcd.publicnode.com'
        
    def create(self) -> LCDClient:
        """
        Create an LCD client instance and store it in this object.
        """

        terra:LCDClient = LCDClient(
            chain_id        = self.chain_id,
            gas_adjustment  = self.gas_adjustment,
            url             = self.url
        )

        self.terra = terra

        return self.terra

    def gasList(self) -> json:
        """
        Make a JSON request for the gas prices, and store it against this LCD client instance.
        """
        if self.gas_price_url is not None:
            gas_list:json = requests.get(self.gas_price_url).json()
        else:
            print (' 🛑 No gas price URL set at self.gas_price_url')
            exit()

        return gas_list
    
    def taxRate(self) -> json:
        """
        Make a JSON request for the tax rate, and store it against this LCD client instance.
        """

        tax_rate:json = requests.get(TAX_RATE_URI).json()
        
        return tax_rate

    def instance(self) -> LCDClient:
        """
        Return the LCD client instance that we have created.
        """
        return self.terra

class Wallet:
    def __init__(self):
        self.address:str      = ''
        self.allow_swaps:bool = True
        self.balances:dict    = {}
        self.delegateTx       = DelegationTransaction()
        self.details:dict     = {}
        self.name:str         = ''
        self.seed:str         = ''
        self.sendTx           = SendTransaction()
        self.swapTx           = SwapTransaction()
        self.terra:LCDClient  = None
        self.validated: bool  = False
        self.withdrawalTx     = WithdrawalTransaction()
        
    def create(self, name, address, seed, password) -> Wallet:
        """
        Create a wallet object based on the provided details.
        """

        self.name    = name
        self.address = address
        self.seed    = cryptocode.decrypt(seed, password)
        self.terra   = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT).create()

        return self
    
    def updateDelegation(self, amount:str, threshold:int) -> bool:
       """
       Update the delegation details with the amount and threshold details.
       """

       self.delegations = {'delegate': amount, 'threshold': threshold}

       return True
    
    def allowSwaps(self, allow_swaps:bool) -> bool
        """
        Update the wallet with the allow_swaps status.
        """

        self.allow_swaps = allow_swaps
        
        return True

    def getBalances(self) -> dict:
        """
        Get the balances associated with this wallet.
        """

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

        return balances

    def validateAddress(self) -> bool:
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

    def getDelegations(self):
        """
        Get the delegations associated with this wallet address.
        """

        self.details = Delegations().create(self.address)

        return self.details
    
    def formatUluna(self, uluna:float, add_suffix:bool = False) -> float|str:
        """
        A generic helper function to convert uluna amounts to LUNC.
        """

        lunc:float = uluna / 1000000

        if add_suffix:
            lunc = str(lunc) + 'LUNC'

        return lunc
    
    def withdrawal(self):
        """
        Update the withdrawal class with the data it needs.
        It will be created via the create() command.
        """

        self.withdrawalTx.seed     = self.seed
        self.withdrawalTx.balances = self.balances

        return self.withdrawalTx
    
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
    
    def delegate(self):
        """
        Update the delegate class with the data it needs
        It will be created via the create() command
        """

        self.delegateTx.seed     = self.seed
        self.delegateTx.balances = self.balances

        return self.delegateTx
    
class Wallets:
    def __init__(self):
        self.file         = None
        self.wallets:dict = {}

    def create(self, yml_file:dict, user_password:str):
        """
        Create a dictionary of wallets. Each wallet is a Wallet object.
        """

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
                wallet_item.allowSwaps = bool(wallet['allow_swaps'])

            wallet_item.validated = wallet_item.validateAddress()

            self.wallets[wallet['wallet']] = wallet_item

        return self
        
    def getWallets(self, validate) -> dict:
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
    
class Delegations(Wallet):

    def __init__(self):        
        self.delegations:dict = {}

    def __iter_result__(self, terra:LCDClient, delegator) -> dict:
        """
        An internal function which returns a dict object with validator details.
        """

        # Get the basic details about the delegator and validator etc
        delegator_address:str       = delegator.delegation.delegator_address
        validator_address:str       = delegator.delegation.validator_address
        validator_details           = terra.staking.validator(validator_address)
        validator_details:Validator = terra.staking.validator(validator_address)
        validator_name:str          = validator_details.description.moniker
        validator_commission:float  = float(validator_details.commission.commission_rates.rate)

        # Get any rewards
        rewards:Rewards   = terra.distribution.rewards(delegator_address)
        reward_coins:dict = coin_list(rewards.rewards[validator_address], {})
        
        # Make the commission human-readable
        validator_commission = round(validator_commission * 100, 2)

        self.delegations[validator_name] = {'delegator': delegator_address, 'validator': validator_address, 'rewards': reward_coins, 'validator_name': validator_name, 'commission': validator_commission}
        
    def create(self, wallet_address:str) -> dict:
        """
        Create a dictionary of information about the delegations on this wallet.
        It may contain more than one validator.
        """

        terra = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT).create()

        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        result, pagination       = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

        delegator:Delegation 
        for delegator in result:
            self.__iter_result__(terra, delegator)

        while pagination['next_key'] is not None:

            pagOpt.key         = pagination['next_key']
            result, pagination = terra.staking.delegations(delegator = wallet_address, params = pagOpt)

            delegator:Delegation 
            for delegator in result:
                self.__iter_result__(terra, delegator)

        return self.delegations
    
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
        self.seed:str                                = ''
        self.sequence:int                            = None
        self.tax_rate:json                           = None
        self.terra                                   = None
        self.transaction:Tx                          = None
        
        # Initialise the basic variables:
        terra         = TerraInstance(GAS_PRICE_URI, GAS_ADJUSTMENT)
        self.terra    = terra.create()
        self.gas_list = terra.gasList()
        self.tax_rate = terra.taxRate()
        
    def calculateFee(self, requested_fee:Fee, use_uusd:bool = False) -> Fee:
        """
        Calculate the fee based on the provided information and what coins are available.
        This function prefers to pay in minor coins first, followed by uluna, and then ustc.

        If desired, the fee can specifically be uusd.
        """

        other_coin_list:list = []
        has_uluna:int        = 0
        has_uusd:int         = 0
        
        coin:Coin
        for coin in requested_fee.amount:
            if coin.denom in self.balances and self.balances[coin.denom] >= coin.amount:

                if coin.denom == 'uusd':
                    has_uusd = coin.amount
                elif coin.denom == 'uluna':
                    has_uluna = coin.amount
                else:
                    other_coin_list.append(coin)

        if has_uluna > 0 or has_uusd > 0 or len(other_coin_list) > 0:
            
            # @TODO: check that this works for random alts
            if len(other_coin_list) > 0:
                requested_fee.amount = Coin(other_coin_list[0].denom, other_coin_list[0].amount)
            elif has_uluna > 0:
                requested_fee.amount = Coin('uluna', has_uluna)
            else:
                requested_fee.amount = Coin('uusd', has_uusd)

            # Override the calculations if we've been told to use uusd
            if use_uusd == True:
                requested_fee.amount = Coin('uusd', has_uusd)
        else:
            print ('Not enough funds to pay for delegation!')

        return requested_fee
    
    def broadcast(self) -> BlockTxBroadcastResult:
        """
        A core broadcast function for all transactions.
        It will wait until the transaction shows up in the search function before finishing.
        """

        result:BlockTxBroadcastResult = self.terra.tx.broadcast(self.transaction)
        self.broadcast_result         = result

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

        return result

class DelegationTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(DelegationTransaction, self).__init__(*args, **kwargs)
        
    def create(self, delegator_address:str, validator_address:str):
        """
        Create a delegation object and set it up with the provided details.
        """

        self.delegator_address = delegator_address
        self.validator_address = validator_address

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        return self
    
    def simulate(self, redelegated_uluna:int) -> bool:
        """
        Simulate a delegation so we can get the fee details.
        The fee details are saved so the actual delegation will work.
        """

        # Set the fee to be None so it is simulated
        self.fee      = None
        self.sequence = self.current_wallet.sequence()
        self.delegate(redelegated_uluna)

        # Store the transaction
        tx:Tx = self.transaction

        # Get the stub of the requested fee so we can adjust it
        requested_fee = tx.auth_info.fee

        # This will be used by the swap function next time we call it
        self.fee = self.calculateFee(requested_fee)

        return True
        

    def delegate(self, redelegated_uluna:int) -> bool:
        """
        Make a delegation with the information we have so far.
        If fee is None then it will be a simulation.
        """

        try:
            msg = MsgDelegate(
                delegator_address   = self.delegator_address,
                validator_address   = self.validator_address,
                amount              = Coin('uluna', redelegated_uluna)
            )

            options = CreateTxOptions(
                fee        = self.fee,
                #fee_denoms  = ['uluna', 'uusd', 'uaud' ,'ukrw'], # 
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
                    self.sequence    = self.sequence + 1
                    options.sequence = self.sequence
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

        self.recipient_address = ''
        self.memo = ''
        self.uluna_amount = 0
        #self.fee_deductables:float = None
        self.tax:float             = None

    def create(self):
        """
        Create a send object and set it up with the provided details.
        """

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        print (self.current_wallet.key.acc_address)
        return self
    
    def simulate(self, recipient_address:str, uluna_amount:int, memo:str) -> bool:
        """
        Simulate a delegation so we can get the fee details.
        The fee details are saved so the actual delegation will work.
        """

        self.recipient_address = recipient_address
        self.memo              = memo
        self.uluna_amount      = uluna_amount

        # Set the fee to be None so it is simulated
        self.fee      = None
        self.sequence = self.current_wallet.sequence()
        self.send()

        # Store the transaction
        tx:Tx = self.transaction

        # Get the stub of the requested fee so we can adjust it
        requested_fee = tx.auth_info.fee

        # This will be used by the swap function next time we call it
        self.fee = self.calculateFee(requested_fee)

        fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
        fee_amount   = fee_bit.amount
        fee_denom    = fee_bit.denom

        # Calculate the tax portion
        self.tax = uluna_amount * float(self.tax_rate['tax_rate'])

        # Build a fee object with 
        new_coin:Coin        = Coin(fee_denom, int(fee_amount + self.tax))
        requested_fee.amount = new_coin

        # This will be used by the swap function next time we call it
        self.fee = requested_fee
        
        return True
        

    def send(self) -> bool:
        """
        Complete a send transaction with the information we have so far.
        If fee is None then it will be a simulation.
        """

        #try:

        msg = MsgSend(
            from_address = self.current_wallet.key.acc_address,
            to_address   = self.recipient_address,
            amount       = Coins(str(self.uluna_amount) + 'uluna')
        )

        options = CreateTxOptions(
            fee        = self.fee,
            #fee_denoms  = ['uluna', 'uusd', 'uaud' ,'ukrw'], # 
            gas_prices = self.gas_list,
            msgs       = [msg],
            sequence   = self.sequence,
            memo = self.memo
        )

        # This process often generates sequence errors. If we get a response error, then
        # bump up the sequence number by one and try again.
        while True:
            try:
                tx:Tx = self.current_wallet.create_and_sign_tx(options)
                break
            except LCDResponseError as err:
                self.sequence    = self.sequence + 1
                options.sequence = self.sequence
            except Exception as err:
                print (' 🛑 A random error has occurred')
                print (err)
                break

        # Store the transaction
        self.transaction = tx

        return True
        #except:
        #    return False
        
class SwapTransaction(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(SwapTransaction, self).__init__(*args, **kwargs)

        self.belief_price          = None
        self.fee_deductables:float = None
        self.max_spread:float      = 0.01
        self.tax:float             = None
        
    def create(self):
        """
        Create a swap object and set it up with the provided details.
        """

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

        return self

    def beliefPrice(self) -> float:
        """
        Figure out the belief price for this swap.
        """

        result = self.terra.wasm.contract_query(UUSD_TO_ULUNA_SWAP_ADDRESS, {"pool": {}})

        belief_price:float = int(result['assets'][0]['amount']) / int(result['assets'][1]['amount']) 

        return round(belief_price, 18)

    def simulate(self) -> bool:
        """
        Simulate a swap so we can get the fee details.
        The fee details are saved so the actual swap will work.
        """

        self.belief_price    = self.beliefPrice()
        self.fee             = None
        self.tax             = None
        self.fee_deductables = None

        # Perform the swap as a simulation, with no fee details
        self.swap()
        
        tx:Tx = self.transaction

        # Get the fee details
        requested_fee:Fee = tx.auth_info.fee

        #print (requested_fee.amount)
        fee_bit:Coin = Coin.from_str(str(requested_fee.amount))

        
        #print ('requested fee:', fee_bit)
        
        #print ('requested_fee amount:', fee_bit.amount)
        #print ('requested_fee denom:', fee_bit.denom)

        fee_amount = fee_bit.amount
        fee_denom = fee_bit.denom

        # Broadcast the transaction (with no fee) so we can get the actual fee options in the error
        simulation_result:BlockTxBroadcastResult = self.broadcast()

        bits = simulation_result.raw_log.strip('(stability): insufficient fee').split('+')

        if len(bits) > 1:
            stability_tax:Coin = Coin.from_str(bits[1].strip('"'))

            #print ('stability coin:', stability_tax)
            #print (stability_tax.amount)

            self.tax = stability_tax.amount

            #fee_amount = stability_tax.amount
            #fee_denom = stability_tax.denom

            #self.tax = Coin(bits[1].strip('"')
        else:
            print ('Error parsing logs - no fee suggestions found')



        # if len(bits) > 1:
        #     fee_bit         = bits[1].split('=')
        #     fee_coins:Coins = Coins.from_str(fee_bit[0].strip(' "'))
        #     self.fee        = self.calculateFee(requested_fee, fee_coins, True)

        # else:
        #     print ('Error parsing logs - no fee suggestions found')

        
        # Get the fee details:
        #fee_coin:Coin = self.calculateFee(requested_fee, True)
        #fee_amount    = fee_coin.amount.amount
        #fee_denom     = fee_coin.amount.denom

        # Take the first fee payment option
        #self.tax = fee_amount * float(self.tax_rate['tax_rate'])
        
        # Build a fee object with 
        new_coin:Coin        = Coin(fee_denom, int(fee_amount + self.tax))
        requested_fee.amount = new_coin

        # This will be used by the swap function next time we call it
        self.fee = requested_fee
        
        #print ('new fee:', self.fee)
        # Store this so we can deduct it off the total amount to swap
        self.fee_deductables = int(fee_amount + self.tax)

        return True
    
    def swap(self) -> bool:
        """
        Make a swap with the information we have so far.
        If fee is None then it will be a simulation.
        """

        if self.belief_price is not None:

            if self.fee is not None:
                fee_denom:str = self.fee.amount.denom
            else:
                fee_denom:str = 'uusd'

            if fee_denom in self.balances:
                swap_amount = self.balances['uusd']

                if self.tax is not None:
                    if fee_denom == 'uusd':
                        swap_amount = swap_amount - self.fee_deductables

                tx_msg = MsgExecuteContract(
                    sender      = self.current_wallet.key.acc_address,
                    contract    = ASTROPORT_UUSD_TO_ULUNA_ADDRESS,
                    execute_msg = {
                        'swap': {
                            'belief_price': str(self.belief_price),
                            'max_spread': str(self.max_spread),
                            'offer_asset': {
                                'amount': str(swap_amount),
                                'info': {
                                    'native_token': {
                                        'denom': 'uusd'
                                    }
                                }
                            },
                        }
                    },
                    coins = Coins(str(swap_amount) + 'uusd')            
                )

                options = CreateTxOptions(
                    fee        = self.fee,
                    # fee_denoms  = ['uluna'],
                    # gas_prices  = {'uluna': self.gas_list['uluna']},
                    fee_denoms = ['uusd'],
                    gas_prices = {'uusd': self.gas_list['uusd']},
                    msgs       = [tx_msg]
                )
                
                while True:
                    try:
                        tx:Tx = self.current_wallet.create_and_sign_tx(options)
                        break
                    except LCDResponseError as err:
                        print (' 🛑 LCD Response Error', err)
                        exit()
                        
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

        # Get the stub of the requested fee so we can adjust it
        requested_fee = tx.auth_info.fee

        # This will be used by the swap function next time we call it
        self.fee = self.calculateFee(requested_fee)

        return True
        

    def withdraw(self) -> bool:
        """
        Make a withdrawal with the information we have so far.
        If fee is None then it will be a simulation.
        """

        try:
            msg = MsgWithdrawDelegatorReward(
                delegator_address = self.delegator_address,
                validator_address = self.validator_address
            )
            
            options = CreateTxOptions(
                fee         = self.fee,
                gas_prices  = self.gas_list,
                msgs        = [msg]
            )

            # This process often generates sequence errors. If we get a response error, then
            # bump up the sequence number by one and try again.
            while True:
                try:
                    tx:Tx = self.current_wallet.create_and_sign_tx(options)
                    break
                except LCDResponseError as err:
                    self.sequence    = self.sequence + 1
                    options.sequence = self.sequence
                except Exception as err:
                    print (' 🛑 A random error has occurred')
                    print (err)
                    break

            # Store the transaction
            self.transaction = tx

            return True
        except:
            return False
    
def main():
    
    # Get the password that decrypts the user wallets
    decrypt_password:str = getpass() # the secret password that encrypts the seed phrase

    # Get the desired actions
    print ('What action do you want to take?')
    print ('  (W)  Withdraw rewards')
    print ('  (S)  Swap coins')
    print ('  (D)  Delegate')
    print ('  (WD) Withdraw & Delegate')
    print ('  (SD) Swap & Delegate')
    print ('  (A)  All of the above')
    print ('  (T)  Send some LUNC to someone')

    user_action = get_user_choice('', ['w', 's', 'd', 'wd', 'sd', 'a', 't'], [])

    try:
        with open(CONFIG_FILE_NAME, 'r') as file:
            user_config = yaml.safe_load(file)
    except :
        print (' 🛑 The user_config.yml file could not be opened - please run configure_user_wallets.py before running this script')
        exit()

    print ('Decrypting and validating wallets - please wait...')

    # Create the wallet object based on the user config file
    wallet_obj = Wallets().create(user_config, decrypt_password)
    
    # Get all the wallets
    user_wallets = wallet_obj.getWallets(True)

    action_string = ''
    if user_action == USER_ACTION_WITHDRAW:
        action_string = 'withdraw rewards'
    if user_action == USER_ACTION_SWAP:
        action_string = 'swap USTC for LUNC'
    if user_action == USER_ACTION_DELEGATE:
        action_string = 'delegate all available funds'
    if user_action == USER_ACTION_WITHDRAW_DELEGATE:
        action_string = 'withdraw rewards and delegating everything'
    if user_action == USER_ACTION_SWAP_DELEGATE:
        action_string = 'swap USTC for LUNC and delegating everything'
    if user_action == USER_ACTION_ALL:
        action_string = 'withdraw rewards, swap USTC for LUNC, and then delegate everything'
    if user_action == USER_ACTION_SEND:
        action_string = 'send some LUNC to different address'

    if action_string == '':
        print (' 🛑 No recognised action to complete, exiting...')
        exit()

    if len(user_wallets) > 0:
        print (f'You can {action_string} on the following wallets:')

        user_wallets,answer = get_user_multichoice("Select a wallet number 1 - " + str(len(user_wallets)) + ", or 'A' to add all of them, 'C' to clear the list, 'X' to continue', and 'Q' to quit: ", user_wallets)

        if answer == 'q':
            print (' 🛑 Exiting...')
            exit()
    else:
        print (' 🛑 This password couldn\'t decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.')
        exit()

    # If we're sending LUNC then we need a few more details:
    if user_action == USER_ACTION_SEND:
        recipient_address = input('What is the address you are sending to? ')
        lunc_amount = input('How much are you sending? ')
        memo = input('Provide a memo (optional): ')

    # Now start doing stuff
    for wallet_name in user_wallets:
        wallet:Wallet = user_wallets[wallet_name]

        print ('####################################')
        print (f'Accessing the {wallet.name} wallet...')

        delegations = wallet.getDelegations()
        for validator in delegations:

            print ('\n------------------------------------')
            print (f"The {delegations[validator]['validator_name']} validator has a {delegations[validator]['commission']}% commission.")

            if user_action in [USER_ACTION_WITHDRAW, USER_ACTION_WITHDRAW_DELEGATE, USER_ACTION_ALL]:

                print ('Starting withdrawals...')

                uluna_reward:int = delegations[validator]['rewards']['uluna']

                # Only withdraw the staking rewards if the rewards exceed the threshold (if any)
                if wallet.formatUluna(uluna_reward, False) > wallet.delegations['threshold']:

                    print (f'Withdrawing {wallet.formatUluna(uluna_reward, False)} rewards')

                    # Update the balances so we know what we have to pay the fee with
                    wallet.getBalances()

                    # Set up the withdrawal object
                    withdrawal_tx = wallet.withdrawal().create(delegations[validator]['delegator'], delegations[validator]['validator'])

                    # Simulate it
                    result = withdrawal_tx.simulate()

                    if result == True:
                        fee_coin:Coin = withdrawal_tx.fee.amount
                        
                        if fee_coin.denom == 'uluna':
                            print (f"Fee is {wallet.formatUluna(int(fee_coin.amount), True)}")
                        else:
                            print (f"Fee is {fee_coin.amount} {fee_coin.denom}")
                            
                        # Now we know what the fee is, we can do it again and finalise it
                        result = withdrawal_tx.withdraw()

                        if result == True:
                            withdrawal_tx.broadcast()
                        
                            if withdrawal_tx.broadcast_result.is_tx_error():
                                print (' 🛎️ Withdrawal failed, an error occurred')
                                print (withdrawal_tx.broadcast_result.raw_log)
                        
                            else:
                                print (f' ✅ Withdrawn amount: {wallet.formatUluna(uluna_reward, True)}')
                                print (f' ✅ Tx Hash: {withdrawal_tx.broadcast_result.txhash}')
                                time.sleep(10)
                    else:
                        print ('The withdrawal could not be completed')
                else:
                    print ('The amount of LUNC in this wallet does not exceed the withdrawal threshold')

            # Swap any uusd coins for uluna
            if user_action in [USER_ACTION_SWAP, USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:

                if wallet.allow_swaps == True:
                    print ('\n------------------------------------')
                    print ('Starting swaps...')

                    # Update the balances so we know we have the correct amount
                    wallet.getBalances()
                    
                    # We are only supporting swaps with uusd (USTC) at the moment
                    swap_amount = wallet.balances['uusd']

                    if swap_amount > 0:
                        print (f'Swapping {wallet.formatUluna(swap_amount, False)} USTC for LUNC')

                        # Set up the basic swap object
                        swaps_tx = wallet.swap().create()

                        # Simulate it so we can get the fee
                        result = swaps_tx.simulate()

                        if result == True:
                            fee_coin:Coin = swaps_tx.fee.amount
                                
                            if fee_coin.denom == 'uluna':
                                print (f"Fee is {wallet.formatUluna(int(fee_coin.amount), True)}")
                            else:
                                print (f"Fee is {fee_coin.amount} {fee_coin.denom}")
                            
                            result = swaps_tx.swap()

                            if result == True:

                                swaps_tx.broadcast()

                                if swaps_tx.broadcast_result.is_tx_error():
                                    print (' 🛎️ Swap failed, an error occurred')
                                    print (swaps_tx.broadcast_result.raw_log)
                            
                                else:
                                    print (f' ✅ Swap successfully completed')
                                    print (f' ✅ Tx Hash: {swaps_tx.broadcast_result.txhash}')
                                    time.sleep(10)
                            else:
                                print ('Swap transaction could not be completed')
                    else:
                        print ('Swap amount is not greater than zero')
                else:
                    print ('Swaps not allowed on this wallet')

            # Redelegate anything we might have
            if user_action in [USER_ACTION_DELEGATE, USER_ACTION_WITHDRAW_DELEGATE, USER_ACTION_SWAP_DELEGATE, USER_ACTION_ALL]:
                
                # Only delegate if the wallet is configured for delegations
                if 'delegate' in wallet.delegations:       

                    print ('\n------------------------------------')
                    print ('Starting delegations...')

                    # Update the balances after having done withdrawals and swaps
                    wallet.getBalances()

                    if 'uluna' in wallet.balances:     

                        # Figure out how much to delegate based on the user settings
                        uluna_balance = int(wallet.balances['uluna'])
                        if wallet.delegations['delegate'].strip(' ')[-1] == '%':
                            percentage:int = int(wallet.delegations['delegate'].strip(' ')[0:-1]) / 100
                            delegated_uluna:int = int(uluna_balance * percentage)
                        else:
                            delegated_uluna:int = wallet.delegations['delegate'].strip(' ')

                        # Adjust this so we have the desired amount still remaining
                        delegated_uluna = int(delegated_uluna - (WITHDRAWAL_REMAINDER * 1000000))

                        if delegated_uluna > 0 and delegated_uluna <= wallet.balances['uluna']:
                            print (f'Delegating {wallet.formatUluna(delegated_uluna, True)}')

                            delegation_tx = wallet.delegate().create(delegations[validator]['delegator'], delegations[validator]['validator'])

                            # Simulate it
                            result = delegation_tx.simulate(delegated_uluna)

                            if result == True:
                                fee_coin:Coin = delegation_tx.fee.amount
                                
                                if fee_coin.denom == 'uluna':
                                    print (f"Fee is {wallet.formatUluna(int(fee_coin.amount), True)}")
                                else:
                                    print (f"Fee is {fee_coin.amount} {fee_coin.denom}")
                                    
                                # Now we know what the fee is, we can do it again and finalise it
                                result = delegation_tx.delegate(delegated_uluna)
                                
                                if result == True:
                                    delegation_tx.broadcast()
                                
                                    if delegation_tx.broadcast_result.is_tx_error():
                                        print (' 🛎️ Delegation failed, an error occurred')
                                        print (delegation_tx.broadcast_result.raw_log)
                                    else:
                                        print (f' ✅ Delegated amount: {wallet.formatUluna(delegated_uluna, True)}')
                                        print (f' ✅ Tx Hash: {delegation_tx.broadcast_result.txhash}')
                                else:
                                    print ('The deleggation could not be completed')
                            else:
                                print ('The delegation could not be completed')
                        else:
                            print ('Delegation error: amount is not greater than zero')
                    else:
                        print ('No LUNC to delegate!')
                else:
                    print ('This wallet is not configured for delegations')

            print (' 💯 All actions on this validator are complete.')
            print ('------------------------------------')

        if user_action == USER_ACTION_SEND:
            # Update the balances after having done withdrawals and swaps
            wallet.getBalances()

            if 'uluna' in wallet.balances:
                # Adjust this so we have the desired amount still remaining
                uluna_amount = int(lunc_amount) * 1000000

                if uluna_amount > 0 and uluna_amount <= (wallet.balances['uluna'] - (WITHDRAWAL_REMAINDER * 1000000)):
                    print (f'Sending {wallet.formatUluna(uluna_amount, True)}')

                    send_tx = wallet.send().create()

                    # Simulate it
                    result = send_tx.simulate(recipient_address, uluna_amount, memo)

                    if result == True:
                        fee_coin:Coin = send_tx.fee.amount
                        
                        if fee_coin.denom == 'uluna':
                            print (f"Fee is {wallet.formatUluna(int(fee_coin.amount), True)}")
                        else:
                            print (f"Fee is {fee_coin.amount} {fee_coin.denom}")
                            
                        # Now we know what the fee is, we can do it again and finalise it
                        result = send_tx.send()
                        
                        if result == True:
                            send_tx.broadcast()
                        
                            if send_tx.broadcast_result.is_tx_error():
                                print (' 🛎️ Send transaction failed, an error occurred')
                                print (send_tx.broadcast_result.raw_log)
                            else:
                                print (f' ✅ Sent amount: {wallet.formatUluna(uluna_amount, True)}')
                                print (f' ✅ Tx Hash: {send_tx.broadcast_result.txhash}')
                        else:
                            print ('The send transaction could not be completed')
                    else:
                        print ('The send transaction could not be completed')
                        
                else:
                    print ('Sending error: Not enough LUNC will be left in the account to cover fees')
            exit()
    print ('Done!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()