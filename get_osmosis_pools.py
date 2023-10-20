
#!/usr/bin/python

import sqlite3
from datetime import datetime

from classes.wallet import UserWallet

from terra_classic_sdk.core.osmosis import Pool, PoolAsset

conn = sqlite3.connect('osmosis.db')
print ("Opened database successfully")

# Create a terra object and get the Osmosis pools
delete_pool_table  = "DROP TABLE IF EXISTS pool;"
delete_asset_table = "DROP TABLE IF EXISTS asset;"
create_pool_table  = "CREATE TABLE pool (ID INTEGER PRIMARY KEY AUTOINCREMENT, date_added DATETIME DEFAULT current_timestamp, pool_id INTEGER NOT NULL, type TEXT NOT NULL, address TEXT NOT NULL, swap_fee FLOAT NOT NULL, exit_fee FLOAT NOT NULL, total_weight INTEGER NOT NULL);"
create_asset_table = "CREATE TABLE asset (ID INTEGER PRIMARY KEY AUTOINCREMENT, date_added DATETIME DEFAULT current_timestamp, pool_id INTEGER NOT NULL, denom TEXT NOT NULL, readable_denom TEXT NOT NULL, amount INTEGER NOT NULL, weight INTEGER NOT NULL);"

add_pool  = "INSERT INTO pool (pool_id, type, address, swap_fee, exit_fee, total_weight) VALUES (?, ?, ?, ?, ?, ?);"
add_asset = "INSERT INTO asset (pool_id, denom, readable_denom, amount, weight) VALUES (?, ?, ?, ?, ?);"

all_pool_ids = "SELECT pool_id FROM pool ORDER BY pool_id ASC;"

wallet:UserWallet = UserWallet().create(denom = 'uosmo')

cursor = conn.execute(delete_pool_table)
cursor = conn.execute(delete_asset_table)
conn.commit()

cursor = conn.execute(create_pool_table)
cursor = conn.execute(create_asset_table)
conn.commit()

pools:list = wallet.terra.pool.osmosis_pools()
pool:Pool
for pool in pools:
    print ('pool id:', pool.id)

    cursor = conn.execute(add_pool, [pool.id, pool.type, pool.address, pool.pool_params.swap_fee, pool.pool_params.exit_fee, pool.total_weight])
    
    pool_asset:PoolAsset
    for pool_asset in pool.pool_assets:
        readable_denom = wallet.denomTrace(pool_asset.token.denom)
            
        if pool_asset.token.denom == 'ibc/785AFEC6B3741100D15E7AF01374E3C4C36F24888E96479B1C33F5C71F364EF9':
            readable_denom = 'uluna2'

        cursor = conn.execute(add_asset, [pool.id, pool_asset.token.denom, readable_denom, pool_asset.token.amount, pool_asset.weight])
        
    conn.commit()

cursor = conn.execute(all_pool_ids)
existing_ids = []
max_id:int = 0
for row in cursor.fetchall():
    existing_ids.append(row[0])
    max_id = row[0]

for i in range(1,max_id):
    if i not in existing_ids:
        try:
            print (f'adding missing pool {i}')
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

conn.close()
exit()
