#!/usr/bin/env python3

import requests
import json
import cryptocode

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

def coin_list(input: Coins, existingList: dict) -> dict:
    """ 
    Converts the Coins list into a dictionary.
    There might be a built-in function for this, but I couldn't get it working.
    """

    coin:Coin
    for coin in input:
        existingList[coin.denom] = coin.amount

    return existingList

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
                wallet_item.allow_swaps = bool(wallet['allow_swaps'])

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
    
    def allowSwaps(self, allow_swaps:bool) -> bool:
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

    def readableFee(self) -> str:
        """
        Return a description of the fee for the current transaction.
        """
        
        fee_coin:Coin = self.fee.amount  
        amount:float  = fee_coin.amount / 1000000

        if fee_coin.denom == 'uluna':
            return (f"Fee is {amount} LUNC")
        elif fee_coin.denom ==' uusd': 
            return (f"Fee is {amount} USTC")
        else:
            return (f"Fee is {amount} {fee_coin.denom}")

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
                delegator_address  = self.delegator_address,
                validator_address  = self.validator_address,
                amount             = Coin('uluna', redelegated_uluna)
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
        self.memo              = ''
        self.uluna_amount      = 0
        self.tax:float         = None

    def create(self):
        """
        Create a send object and set it up with the provided details.
        """

        # Create the wallet based on the calculated key
        current_wallet_key  = MnemonicKey(self.seed)
        self.current_wallet = self.terra.wallet(current_wallet_key)

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

        # Figure out the fee structure
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

        # Get the stub of the requested fee so we can adjust it
        requested_fee = tx.auth_info.fee

        # This will be used by the swap function next time we call it
        self.fee = self.calculateFee(requested_fee)

        # Figure out the fee structure
        fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
        fee_amount   = fee_bit.amount
        fee_denom    = fee_bit.denom

        swap_amount = self.balances['uusd']

        # Calculate the tax portion
        self.tax = swap_amount * float(self.tax_rate['tax_rate'])

        # Build a fee object with 
        new_coin:Coin        = Coin(fee_denom, int(fee_amount + self.tax))
        requested_fee.amount = new_coin

        # This will be used by the swap function next time we call it
        self.fee = requested_fee
        
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