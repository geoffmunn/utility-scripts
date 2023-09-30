
#!/usr/bin/python

import sqlite3
from datetime import datetime

from utility_classes import (
    Wallet
)

from terra_classic_sdk.core.osmosis import Pool, PoolAsset

conn = sqlite3.connect('osmosis.db')
print ("Opened database successfully")

# Create a terra object and get the Osmosis pools
delete_pool_table  = "DROP TABLE IF EXISTS pool;"
delete_asset_table = "DROP TABLE IF EXISTS asset;"
create_pool_table  = "CREATE TABLE pool (ID INTEGER PRIMARY KEY AUTOINCREMENT, pool_id INTEGER NOT NULL, type TEXT NOT NULL, address TEXT NOT NULL, swap_fee FLOAT NOT NULL, exit_fee FLOAT NOT NULL, total_weight INTEGER NOT NULL);"
create_asset_table = "CREATE TABLE asset (ID INTEGER PRIMARY KEY AUTOINCREMENT, pool_id INTEGER NOT NULL, denom TEXT NOT NULL, readable_denom TEXT NOT NULL, amount INTEGER NOT NULL, weight INTEGER NOT NULL);"

add_pool  = "INSERT INTO pool (pool_id, type, address, swap_fee, exit_fee, total_weight) VALUES (?, ?, ?, ?, ?, ?);"
add_asset = "INSERT INTO asset (pool_id, denom, readable_denom, amount, weight) VALUES (?, ?, ?, ?, ?);"

cursor = conn.execute(delete_pool_table)
cursor = conn.execute(delete_asset_table)
conn.commit()
cursor = conn.execute(create_pool_table)
cursor = conn.execute(create_asset_table)
conn.commit()

wallet:Wallet = Wallet().create(prefix = 'osmo')

pools:list = wallet.terra.pool.osmosis_pools()

pool:Pool
for pool in pools:
    vals:list = []
    vals.append(pool.id)
    vals.append(pool.type)
    vals.append(pool.address)
    vals.append(pool.pool_params.swap_fee)
    vals.append(pool.pool_params.exit_fee)
    vals.append(pool.total_weight)

    cursor = conn.execute(add_pool, vals)
    conn.commit()

    pool_asset:PoolAsset
    for pool_asset in pool.pool_assets:
        denom_trace = wallet.denomTrace(pool_asset.token.denom)
        if denom_trace == False:
            readable_denom = pool_asset.token.denom
        else:
            readable_denom = denom_trace['base_denom']
            
        if pool_asset.token.denom == 'ibc/785AFEC6B3741100D15E7AF01374E3C4C36F24888E96479B1C33F5C71F364EF9':
            readable_denom = 'uluna2'

        asset:list = []
        asset.append(pool.id)
        asset.append(pool_asset.token.denom)
        asset.append(readable_denom)
        asset.append(pool_asset.token.amount)
        asset.append(pool_asset.weight)
        cursor = conn.execute(add_asset, asset)
        conn.commit()

conn.close()
exit()

####

# CREATE INDEX history_date_added ON history (date_added);
# CREATE INDEX history_coin_id ON history (coin_id);
# CREATE INDEX coin_coin_id ON coin (coin_id); 
# CREATE UNIQUE INDEX category_id ON category (category_id);

#SELECT pool.pool_id, readable_denom, swap_fee FROM pool INNER JOIN asset ON pool.pool_id=asset.pool_id WHERE pool.pool_id IN (SELECT pool_id FROM asset WHERE readable_denom = 'uluna') AND readable_denom='uosmo' ORDER BY swap_fee ASC;

#SELECt pool.pool_id, readable_denom, swap_fee FROM pool INNER JOIN asset ON pool.pool_id=asset.pool_id WHERE pool.pool_id IN (SELECT pool_id FROM asset WHERE readable_denom = 'uosmo') and readable_denom='ukuji' ORDER BY swap_fee ASC;



