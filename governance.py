#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from classes.common import (
    check_version,
    get_user_choice
)

from constants.constants import (
    CHAIN_DATA,
    FULL_COIN_LOOKUP,
    ULUNA,
    UOSMO,
    USER_ACTION_CONTINUE,
    USER_ACTION_QUIT,
    PROPOSAL_VOTE_EMPTY,
    PROPOSAL_VOTE_YES,
    PROPOSAL_VOTE_ABSTAIN,
    PROPOSAL_VOTE_NO,
    PROPOSAL_VOTE_NO_WITH_VETO
)

from classes.governance import Governance, cast_governance_vote
from classes.transaction_core import TransactionResult
from classes.wallet import UserWallet
from classes.wallets import UserWallets

def main():
    
    # Check if there is a new version we should be using
    check_version()

    # Get the user wallets
    wallets = UserWallets()
    user_wallets:dict = wallets.loadUserWallets(get_balances = False)
    
    if len(user_wallets) > 0:
        print (f'You can vote on the following proposals:')

        # Create the governance object
        governance:Governance = Governance().create()

        # Get any proposals that are up for voting
        proposals:dict = governance.proposals()

        if len(proposals) > 0:
            proposal, answer = governance.getUserSingleChoice(f"Select a proposal number 1 - {str(len(proposals))}, 'X' to continue, or 'Q' to quit: ")
        else:
            print ('\n 🛑 There are no active proposals to vote on at the moment.\n')
            exit()

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()

    # Get the wallets we'll be making votes on
    user_wallets, answer = wallets.getUserMultiChoice(f"Select a wallet number 1 - {str(len(user_wallets))}, or 'A' to add all of them, 'C' to clear the list, 'X' to continue, or 'Q' to quit: ", {'display': 'votes', 'proposal_id': proposal['id']})

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    # Get the user vote:
    vote_options:dict = {
        #'c': PROPOSAL_VOTE_EMPTY,
        'y': PROPOSAL_VOTE_YES,
        'a': PROPOSAL_VOTE_ABSTAIN,
        'n': PROPOSAL_VOTE_NO,
        'v': PROPOSAL_VOTE_NO_WITH_VETO,
        'q': -1
    }

    print ('What is your vote going to be?\n')
    #print ('  (C)  Clear my existing vote')
    print ('  (Y)  Vote yes')
    print ('  (A)  Abstain')
    print ('  (N)  Vote no')
    print ('  (V)  No with veto')
    print ('  (Q)  Quit')
    print ('')
    
    user_vote = get_user_choice(' ❓ Pick a vote option: ', vote_options.keys())
        
    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    # Get a memo value from the user
    memo:str = UserWallet().getUserText('\n 🖊  Provide a memo (optional): ', 255, True)

    transaction_results:dict = cast_governance_vote(user_wallets, proposal['id'], vote_options[user_vote], memo)

    for transaction_result in transaction_results:
        transaction:TransactionResult = transaction_results[transaction_result]
        print ('')
        transaction.showResults()
        # transaction:TransactionResult = transaction_results[transaction_result]
        # print ('')
        # if transaction.transaction_confirmed == True:
        #     print (f' ✅ Vote successful on the {transaction_result} wallet!')
        #     print (f' ✅ Tx Hash: {transaction.broadcast_result.txhash}\n')
        # else:
        #     print (f' 🛎️  An error occured on the {transaction_result} wallet.')
        #     print (transaction.message)
        #     if transaction.code is not None:
        #         print (transaction.code)
        #     if transaction.log is not None:
        #         print (transaction.log)

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()