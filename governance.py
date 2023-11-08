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

from classes.governance import Governance
from classes.wallet import UserWallet
from classes.wallets import UserWallets

def main():
    
    # Check if there is a new version we should be using
    check_version()

    

    #for prop in proposals:
    #   print (prop)

    # Get the user wallets
    wallets = UserWallets()
    user_wallets = wallets.loadUserWallets()
    
    if len(user_wallets) > 0:
        print (f'You can vote on the following proposals:')

        # Create the governance object
        governance:Governance = Governance().create()
        proposals:dict = governance.proposals()

        proposal, answer = governance.getUserSingleChoice(f"Select a proposal number 1 - {str(len(proposals))}, 'X' to continue, or 'Q' to quit: ")

        if answer == USER_ACTION_QUIT:
            print (' 🛑 Exiting...\n')
            exit()
    else:
        print (" 🛑 This password couldn't decrypt any wallets. Make sure it is correct, or rebuild the wallet list by running the configure_user_wallet.py script again.\n")
        exit()


    
    # Get the user wallets
    # wallets = UserWallets()
    # user_wallets:UserWallets = wallets.loadUserWallets()

    # # Create the governance object
    # governance:Governance = Governance().create()

    # # Get all the proposals currently taking votes
    # proposals:dict = governance.proposals()

    user_wallets, answer = wallets.getUserMultiChoice(f"Select a wallet number 1 - {str(len(user_wallets))}, or 'A' to add all of them, 'C' to clear the list, 'X' to continue, or 'Q' to quit: ")

    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    # Get the user vote:
    vote_options:dict = {
        'c': PROPOSAL_VOTE_EMPTY,
        'y': PROPOSAL_VOTE_YES,
        'a': PROPOSAL_VOTE_ABSTAIN,
        'n': PROPOSAL_VOTE_NO,
        'c': PROPOSAL_VOTE_NO_WITH_VETO,
        'q': -1
    }

    print ('What is your vote going to be?\n')
    print ('  (C)  Clear my existing vote')
    print ('  (Y)  Vote yes')
    print ('  (A)  Abstain')
    print ('  (N)  Vote no')
    print ('  (V)  No with veto')
    print ('  (Q)  Quit')

    print (vote_options.keys())
    user_choice = get_user_choice('Pick a vote option: ', vote_options.keys())
        
    if answer == USER_ACTION_QUIT:
        print (' 🛑 Exiting...\n')
        exit()

    governance.proposal_id = proposal['id']
    governance.user_vote = vote_options[user_choice]

    for wallet_name in user_wallets:

        wallet:UserWallet = user_wallets[wallet_name]
        wallet.getBalances()

        governance.balances = wallet.balances
        governance.update(wallet.seed)

        governance.simulate()
        result = governance.vote()

        if result == True:
            governance.broadcast()

            if governance.broadcast_result is not None and governance.broadcast_result.code == 32:
                while True:
                    print (' 🛎️  Boosting sequence number and trying again...')

                    governance.sequence = governance.sequence + 1
                    
                    governance.simulate()
                    governance.send()
                        
                    governance.broadcast()

                    if governance is None:
                        break

                    # Code 32 = account sequence mismatch
                    if governance.broadcast_result.code != 32:
                        break

            if governance.broadcast_result is None or governance.broadcast_result.is_tx_error():
                if governance.broadcast_result is None:
                    print (' 🛎️  The vote transaction failed, no broadcast object was returned.')
                else:
                    print (' 🛎️  The vote transaction failed, an error occurred:')
                    if governance.broadcast_result.raw_log is not None:
                        print (f' 🛎️  Error code {governance.broadcast_result.code}')
                        print (f' 🛎️  {governance.broadcast_result.raw_log}')
                    else:
                        print ('No broadcast log was available.')
            else:
                if governance.result_received is not None:
                    print (f' ✅ Tx Hash: {governance.broadcast_result.txhash}')
        else:
            print (' 🛎️  The vote transaction could not be completed')

    print (' 💯 Done!\n')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()