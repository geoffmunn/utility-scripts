
#!/usr/bin/python

import sqlite3

from constants.constants import (
    DB_FILE_NAME
)

from classes.wallet import UserWallet

from terra_classic_sdk.core.osmosis import Pool, PoolAsset

def main():
    conn = sqlite3.connect(DB_FILE_NAME)
    print ("Opened database successfully")

    # Create a terra object and get the Osmosis pools
    delete_pool_table    = "DROP TABLE IF EXISTS pool;"
    delete_asset_table   = "DROP TABLE IF EXISTS asset;"
    delete_summary_table = "DROP TABLE IF EXISTS osmosis_summary;"

    create_pool_table    = "CREATE TABLE pool (ID INTEGER PRIMARY KEY AUTOINCREMENT, date_added DATETIME DEFAULT CURRENT_TIMESTAMP, pool_id INTEGER NOT NULL, type TEXT NOT NULL, address TEXT NOT NULL, swap_fee FLOAT NOT NULL, exit_fee FLOAT NOT NULL, total_weight INTEGER NOT NULL);"
    create_asset_table   = "CREATE TABLE asset (ID INTEGER PRIMARY KEY AUTOINCREMENT, date_added DATETIME DEFAULT CURRENT_TIMESTAMP, pool_id INTEGER NOT NULL, denom TEXT NOT NULL, readable_denom TEXT NOT NULL, amount INTEGER NOT NULL, weight INTEGER NOT NULL);"
    create_summary_table = "CREATE TABLE osmosis_summary (ID INTEGER PRIMARY KEY AUTOINCREMENT, last_scan_date DATETIME);"

    add_pool       = "INSERT INTO pool (pool_id, type, address, swap_fee, exit_fee, total_weight) VALUES (?, ?, ?, ?, ?, ?);"
    add_asset      = "INSERT INTO asset (pool_id, denom, readable_denom, amount, weight) VALUES (?, ?, ?, ?, ?);"
    update_summary = "INSERT INTO osmosis_summary (last_scan_date) VALUES (CURRENT_TIMESTAMP);"

    all_pool_ids = "SELECT pool_id FROM pool ORDER BY pool_id ASC;"

    wallet:UserWallet = UserWallet().create(denom = 'uosmo')

    cursor = conn.execute(delete_pool_table)
    cursor = conn.execute(delete_asset_table)
    cursor = conn.execute(delete_summary_table)
    conn.commit()

    cursor = conn.execute(create_pool_table)
    cursor = conn.execute(create_asset_table)
    cursor = conn.execute(create_summary_table)
    conn.commit()

    pools:list = wallet.terra.pool.osmosis_pools()
    pool:Pool
    for pool in pools:
        print (f'Adding pool id {pool.id}')
        cursor = conn.execute(add_pool, [pool.id, pool.type, pool.address, pool.pool_params.swap_fee, pool.pool_params.exit_fee, pool.total_weight])
        
        pool_asset:PoolAsset
        for pool_asset in pool.pool_assets:
            readable_denom = wallet.denomTrace(pool_asset.token.denom)
                
            if pool_asset.token.denom == 'ibc/785AFEC6B3741100D15E7AF01374E3C4C36F24888E96479B1C33F5C71F364EF9':
                readable_denom = 'uluna2'

            cursor = conn.execute(add_asset, [pool.id, pool_asset.token.denom, readable_denom, pool_asset.token.amount, pool_asset.weight])
            
        conn.commit()

    cursor            = conn.execute(all_pool_ids)
    existing_ids:list = []
    max_id:int        = 0

    for row in cursor.fetchall():
        existing_ids.append(row[0])
        max_id = row[0]

    for i in range(1,max_id):
        if i not in existing_ids:
            try:
                print (f'Adding missing pool {i}')
                pool = wallet.terra.pool.osmosis_pool(i)

                cursor = conn.execute(add_pool, [pool.id, pool.type, pool.address, pool.pool_params.swap_fee, pool.pool_params.exit_fee, pool.total_weight])
                
                pool_asset:PoolAsset
                for pool_asset in pool.pool_assets:
                    readable_denom = wallet.denomTrace(pool_asset.token.denom)
                        
                    if pool_asset.token.denom == 'ibc/785AFEC6B3741100D15E7AF01374E3C4C36F24888E96479B1C33F5C71F364EF9':
                        readable_denom = 'uluna2'

                    cursor = conn.execute(add_asset, [pool.id, pool_asset.token.denom, readable_denom, pool_asset.token.amount, pool_asset.weight])
                    
                conn.commit()
            except Exception as err:
                print (err)

    # Update the summary:
    cursor = conn.execute(update_summary, [])
    conn.commit()

    conn.close()

    print ('Finished!')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()