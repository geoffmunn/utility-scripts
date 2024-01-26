#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json

from constants.constants import (
    CHAIN_DATA,
    ULUNA,
    USER_ACTION_QUIT,
    PROPOSAL_STATUS_VOTING_PERIOD
    
)

from classes.terra_instance import TerraInstance
from classes.transaction_core import TransactionCore, TransactionResult
from classes.wallet import UserWallet

from terra_classic_sdk.core.coin import Coin
from terra_classic_sdk.core.coins import Coins
from terra_classic_sdk.core.fee import Fee
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.params import PaginationOptions
from terra_classic_sdk.core.gov import MsgVote, Proposal
from terra_classic_sdk.key.mnemonic import MnemonicKey
from terra_classic_sdk.client.lcd.api.tx import (
    CreateTxOptions,
    Tx
)
class Governance(TransactionCore):

    def __init__(self, *args, **kwargs):

        super(Governance, self).__init__(*args, **kwargs)

        self.account_number:int = None
        self.address:str        = None
        self.fee:Fee            = None
        self.gas_list:json      = None
        self.gas_limit:str      = 'auto'
        self.memo:str           = ''
        self.proposal_id:int    = None
        self.terra:LCDClient    = None
        self.user_vote:int      = None
        self.sequence:int       = None

    def create(self):
        """
        Create a basic terra LCDClient object
        """

        # Defaults to uluna/terra
        self.terra = TerraInstance().create()

        return self
    
    def getUserSingleChoice(self, question:str):
        """
        Get a single user selection from a list.
        This is a custom function because the options are specific to this list.
        """

        # Get the active proposals:
        proposals:dict = self.proposals()

        # Get the longest proposal name:
        label_widths:list = []

        label_widths.append(len('Number'))
        label_widths.append(len('ID'))
        label_widths.append(len('Title'))
        label_widths.append(len('Yes  '))
        label_widths.append(len('No   ')) # extra space is deliberate
        label_widths.append(len('No with veto'))
        label_widths.append(len('Abstain'))
        
        tallies:dict = {}
        for proposal in proposals:
            if len(str(proposal['id'])) > label_widths[1]:
                label_widths[1] = len(str(proposal['id']))
            if len(str(proposal['title'])) > label_widths[2]:
                label_widths[2] = len(str(proposal['title']))

            # Go and get the tally results so we don't have to slow the display refresh down
            self.proposal_id = int(proposal['id'])
            tallies[proposal['id']] = self.tally()

        padding_str:str   = ' ' * 100
        header_string:str = ' Number'

        # Add the other columns to the header string
        header_string += ' | ID' + padding_str[0:label_widths[1] - len('ID')]
        header_string += ' | Title' + padding_str[0:label_widths[2] - len('Title')]
        header_string += ' | Yes   | No    | No with veto | Abstain'

        horizontal_spacer:str = '-' * (len(header_string) + 2)

        proposal_to_use:int = None
        while True:
            count:int = 0

            print (horizontal_spacer)
            print (header_string)
            print (horizontal_spacer)

            for proposal in proposals:
                count += 1
                
                self.proposal_id = int(proposal['id'])

                glyph:str = '  '
                if count == proposal_to_use:
                    glyph = '✅'
                
                count_str:str          = f' {count}' + padding_str[0:6 - (len(str(count)) + 2)]
                proposal_id_str:str    = str(proposal['id']) + padding_str[0:label_widths[1] - len(str(proposal['id']))]
                proposal_title_str:str = proposal['title'] + padding_str[0:label_widths[2] - len(proposal['title'])]
                
                #votes = self.tally()
                votes = tallies[proposal['id']]
                yes_str          = str(votes['yes']) + padding_str[0:label_widths[3] - len(str(votes['yes']))]
                no_str           = str(votes['no']) + padding_str[0:label_widths[4] - len(str(votes['no']))]
                no_with_veto_str = str(votes['no with veto']) + padding_str[0:label_widths[5] - len(str(votes['no with veto']))]
                abstain_str      = str(votes['abstain']) + padding_str[0:label_widths[6] - len(str(votes['abstain']))]
                
                print (f"{count_str}{glyph} | {proposal_id_str} | {proposal_title_str} | {yes_str} | {no_str} | {no_with_veto_str} | {abstain_str}")

            print (horizontal_spacer + '\n')

            answer:str = input(question).lower()
            
            if answer.isdigit() and (0 < int(answer) < (len(proposals) + 1)):
                proposal_to_use = int(answer)

            if answer == 'x':
                if proposal_to_use > 0:
                    break
                else:
                    print ('\nPlease select a proposal first.\n')

            if answer == USER_ACTION_QUIT:
                break

        if proposal_to_use is not None:
            return proposals[proposal_to_use - 1], answer
        else:
            return None, answer
    
    def tally(self) -> dict:
        """
        Get the vote percentages of the current proposal ID
        """

        votes = {'yes': 0, 'no': 0, 'no with veto': 0, 'abstain': 0}

        if self.proposal_id is not None:
        
            tally:dict = self.terra.gov.tally(self.proposal_id)

            total:int = 0
            for item in tally:
                total += int(tally[item])

            votes['yes']          = round((int(tally['yes_count']) / total) * 100, 2)
            votes['no']           = round((int(tally['no_count']) / total) * 100, 2)
            votes['no with veto'] = round((int(tally['no_with_veto_count']) / total) * 100, 2)
            votes['abstain']      = round((int(tally['abstain_count']) / total) * 100, 2)

        return votes

    def proposals(self) -> list:
        """
        Create a dictionary of all the active proposals
        """
        
        proposal_list:list = []
        
        # The parameters we pass. You can do pagination & filters at the same time apparently.
        pagOpt:PaginationOptions = PaginationOptions(limit=50, count_total=True)
        proposal_params:dict     = {'proposal_status': PROPOSAL_STATUS_VOTING_PERIOD}

        # Pass the parameters in the correct order:
        result, pagination = self.terra.gov.proposals(proposal_params, pagOpt)

        proposal:Proposal
        for proposal in result:
            if type(proposal) == Proposal:
                proposal_list.append({'id': proposal.proposal_id, 'title': proposal.content.title, 'content': proposal.content.description, 'voting_start': proposal.voting_start_time, 'voting_end': proposal.voting_end_time})

        while pagination["next_key"] is not None:
            pagOpt             = PaginationOptions(key = pagination["next_key"])
            result, pagination = self.terra.gov.proposals(proposal_params, pagOpt)
            for proposal in result:
                if type(proposal) == Proposal:
                    proposal_list.append({'id': proposal.proposal_id, 'title': proposal.content.title, 'content': proposal.content.description, 'voting_start': proposal.voting_start_time, 'voting_end': proposal.voting_end_time})

        return proposal_list
    
    def simulate(self):
        """
        Simulate a vote so we can get the fee details.
        """

        # Reset these values in case this is a re-used object:
        self.account_number:int = self.current_wallet.account_number()
        self.fee:Fee            = None
        self.gas_limit:str      = 'auto'
        self.sequence:int       = self.current_wallet.sequence()
        
        # Perform the swap as a simulation, with no fee details
        self.vote()

        # Store the transaction
        tx:Tx = self.transaction

        if tx is not None:
            # Get the stub of the requested fee so we can adjust it
            requested_fee:Fee = tx.auth_info.fee

            # This will be used by the swap function next time we call it
            # We'll use uluna as the preferred fee currency just to keep things simple
            self.fee = self.calculateFee(requested_fee = requested_fee, specific_denom = ULUNA)
            
            # Figure out the fee structure
            fee_bit:Coin = Coin.from_str(str(requested_fee.amount))
            fee_amount   = fee_bit.amount
            fee_denom    = fee_bit.denom

            new_coin:Coins = Coins({Coin(fee_denom, int(fee_amount))})
                
            requested_fee.amount = new_coin
            
            # This will be used by the swap function next time we call it
            self.fee = requested_fee
        
            return True
        else:
            return False
        
    def update(self, seed:str):
        """
        Update this object with the wallet details that we want to cast votes on.
        This allows us to reuse the existing Terra connection.
        """

        # Create the wallet based on the calculated key
        prefix                         = CHAIN_DATA[ULUNA]['bech32_prefix']
        current_wallet_key:MnemonicKey = MnemonicKey(mnemonic = seed, prefix = prefix)
        self.current_wallet            = self.terra.wallet(current_wallet_key)
        
        # Assign the wallet address to this governance object
        self.address = current_wallet_key.acc_address

        # Get the gas prices and tax rate:
        self.gas_list = self.gasList()

        return self
    
    def vote(self):
        """
        Cast the vote with the details provided by the user.
        The simulate function needs to have been called first.
        """

        msg = MsgVote(
            proposal_id = self.proposal_id,
            voter       = self.address,
            option      = self.user_vote
        )
            
        options = CreateTxOptions(
            account_number = str(self.account_number),
            gas            = self.gas_limit,
            gas_prices     = self.gas_list,
            fee            = self.fee,
            memo           = self.memo,
            msgs           = [msg],
            sequence       = str(self.sequence)
        )

        # This process often generates sequence errors. If we get a response error, then
        # bump up the sequence number by one and try again.
        tx:Tx = None
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
                    print (' 🛑 An unexpected error occurred in the governance vote function:')
                    print (err)
                    break
            except Exception as err:
                print (' 🛑 An unexpected error occurred in the governance vote function:')
                print (err)
                break

        # Store the transaction
        self.transaction = tx

        return True
    
def cast_governance_vote(user_wallets:dict, proposal_id:int, user_vote:int, memo:str = '' ):
    """
    A wrapper function for casting governance votes.
    The wrapper function adds any error messages depending on the results that got returned.
    
    @params:
      - user_wallets: a dictionary of all the wallets we're voting with
      - proposal_id: the id of the proposal ID we're voting on
      - user_vote: one of the values in the PROPOSAL constant list
      - memo: an optional message to include. Defaults to an empty string.

    @returns a transaction_result object
    """

    transaction_result:TransactionResult = TransactionResult()

    governance:Governance = Governance().create()

    governance.proposal_id = proposal_id
    governance.user_vote   = user_vote
    governance.memo        = memo

    for wallet_name in user_wallets:

        wallet:UserWallet = user_wallets[wallet_name]
        wallet.getBalances()

        governance.balances = wallet.balances
        governance.update(wallet.seed)

        governance.simulate()
        governance_result = governance.vote()

        if governance_result == True:
            transaction_result = governance.broadcast()

            if transaction_result.broadcast_result is not None and transaction_result.broadcast_result.code == 32:
                while True:
                    print (' 🛎️  Boosting sequence number and trying again...')

                    governance.sequence = governance.sequence + 1
                    
                    governance.simulate()
                    governance.send()
                    transaction_result = governance.broadcast()

                    if governance is None:
                        break

                    # Code 32 = account sequence mismatch
                    if transaction_result.broadcast_result.code != 32:
                        break

            if transaction_result.broadcast_result is None or transaction_result.broadcast_result.is_tx_error():
                if transaction_result.broadcast_result is None:
                    transaction_result.message = ' 🛎️  The vote transaction failed, no broadcast object was returned.'
                else:
                    if transaction_result.broadcast_result.raw_log is not None:
                        transaction_result.message = f' 🛎️  {transaction_result.broadcast_result.raw_log}'
                    else:
                        transaction_result.message = 'No broadcast log was available.'
        else:
            transaction_result.message = ' 🛎️  The vote transaction could not be completed'

    return transaction_result
