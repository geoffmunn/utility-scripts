
#!/usr/bin/python

import sqlite3
import json

from constants.constants import (
    DB_FILE_NAME
)

from classes.wallet import UserWallet
from classes.wallets import UserWallets

from classes.swap_transaction import SwapTransaction, swap_coins
from classes.transaction_core import TransactionResult

from terra_classic_sdk.core.coin import Coin

def main():
    conn = sqlite3.connect(DB_FILE_NAME)
    conn.row_factory = sqlite3.Row
    print ("Opened database successfully")

    get_open_trades = "SELECT ID, date_added, wallet_name, coin_from, amount_from, price_from, coin_to, amount_to, price_to, fees, exit_profit, exit_loss FROM trades WHERE status = 'OPEN' and coin_to='urakoff';"
    update_trade = "UPDATE trades SET linked_trade_id=?, status=? WHERE ID=?;"

    wallets = UserWallets()
    user_wallets = wallets.loadUserWallets()
    cursor = conn.cursor()
    cursor = conn.execute(get_open_trades)
    
    for open_trades_row in cursor.fetchall():
        
        wallet:UserWallet = None
        if open_trades_row['wallet_name'] in user_wallets:
            wallet = user_wallets[open_trades_row['wallet_name']]
        
        if wallet is not None:

            
            #print (open_trades_row['exit_profit'])

            original_trade_id:int = open_trades_row['ID']

            print ('*************')

            #print (open_trades_row)
            # for x in open_trades_row.keys():
            #    print (x, open_trades_row[x])

            
            print (f"Wallet: {open_trades_row['wallet_name']} (database row id {original_trade_id})\n")
            print (f"You purchased {wallet.formatUluna(open_trades_row['amount_to'], open_trades_row['coin_to'], True)} with {wallet.formatUluna(open_trades_row['amount_from'], open_trades_row['coin_from'], True)}")

            incoming_fees = json.loads(open_trades_row['fees'])['LUNC']
            
            # Set up the swap details
            swap_tx = SwapTransaction().create(wallet.seed, wallet.denom)

            swap_tx.swap_amount        = float(wallet.formatUluna(open_trades_row['amount_to'], open_trades_row['coin_to'], False))
            swap_tx.swap_denom         = open_trades_row['coin_to']
            swap_tx.swap_request_denom = open_trades_row['coin_from']
            swap_tx.wallet_denom       = wallet.denom

            # Change the contract depending on what we're doing
            swap_tx.setContract()
            
            estimated_value:float = swap_tx.swapRate()
            
            
            profit_target_value =  float(wallet.formatUluna(open_trades_row['amount_from'], open_trades_row['coin_from'])) + float(wallet.formatUluna(open_trades_row['amount_from'] * open_trades_row['exit_profit'], open_trades_row['coin_from']))
            loss_target_value = float(wallet.formatUluna(open_trades_row['amount_from'], open_trades_row['coin_from'])) + float(wallet.formatUluna(open_trades_row['amount_from'] * open_trades_row['exit_loss'], open_trades_row['coin_from']))

            print (f'Not including swap fees, this is now worth {estimated_value}')
            print ('---')
            print (f'This will be automatically sold at a profit when it is at {profit_target_value}')
            print (f'This will be automatically sold at a loss when it is at {loss_target_value}')

            print (f'Swap fees are expected to be {float(incoming_fees) * 2}')

            # Get the current decision:
            swap_coin:Coin = Coin(open_trades_row['coin_to'], open_trades_row['amount_to'])

            if estimated_value >= profit_target_value:
                print ('WE NEED TO SELL FOR A PROFIT')
                
                wallet.getBalances()

                #print ('swap coin:', swap_coin)
                #print (open_trades_row['coin_from'])
                transaction_result:TransactionResult = swap_coins(wallet, swap_coin, open_trades_row['coin_from'], 0, True, True)

                trade_id:int = transaction_result.trade_id

                #print ('closing trade id:', trade_id)
                # Update the original trade row with this ID, and mark it as being closed
                conn.execute(update_trade, [original_trade_id, 'CLOSED', trade_id])
                conn.execute(update_trade, [trade_id, 'CLOSED', original_trade_id])
                conn.commit()

                transaction_result.showResults()
                
            elif estimated_value <= loss_target_value:
                print ('WE NEED TO SELL AT A LOSS')

                # transaction_result:TransactionResult = swap_coins(wallet, swap_coin, open_trades_row['coin_from'], '', False, True)

                # trade_id:int = transaction_result.trade_id

                # # Update the original trade row with this ID, and mark it as being closed
                # conn.execute(update_trade, [trade_id, original_trade_id])
                # conn.commit()
                
                # transaction_result.showResults()

            else:
                print ('do nothing, keep waiting')

            print ('')
    conn.close()

    print ('Finished!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()