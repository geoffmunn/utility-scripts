#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# User settings - can be changed if required
CHECK_FOR_UPDATES    = True
WITHDRAWAL_REMAINDER = 250   # This is the amount of Lunc we want to keep after withdrawal and before delegating. You should never delegate the entire balance.
SEARCH_RETRY_COUNT   = 30    # This is the number of times we will check for a transaction to appear in the chain before deciding it didn't work.

# System settings - these can be changed, but shouldn't be necessary
GAS_PRICE_URI            = 'https://terra-classic-fcd.publicnode.com/v1/txs/gas_prices'
TAX_RATE_URI             = 'https://terra-classic-lcd.publicnode.com/terra/treasury/v1beta1/tax_rate'
TOKEN_LIST               = 'https://assets.terrarebels.net/cw20/tokens.json'
CONFIG_FILE_NAME         = 'user_config.yml'
GAS_ADJUSTMENT           = 3.6
GAS_ADJUSTMENT_SEND      = 3.6
GAS_ADJUSTMENT_SWAPS     = 3.6
GAS_ADJUSTMENT_INCREMENT = 0.1
MAX_GAS_ADJUSTMENT       = 4
VERSION_URI              = 'https://raw.githubusercontent.com/geoffmunn/utility-scripts/main/version.json'

# Swap contracts can be found here
# https://assets.terra.money/cw20/pairs.dex.json
TERRASWAP_UUSD_TO_ULUNA_ADDRESS = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
#TERRASWAP_UKRW_TO_UUSD_ADDRESS  = 'terra1untf85jwv3kt0puyyc39myxjvplagr3wstgs5s'
#ASTROPORT_UUSD_TO_MINA_ADDRESS  = 'terra134m8n2epp0n40qr08qsvvrzycn2zq4zcpmue48'
#ASTROPORT_UUSD_TO_UKUJI_ADDRESS  = 'terra1hasy32pvxmgu485x5tujylemqxynsv72lsu7ve'
#ASTROPORT_UUSD_TO_ULUNA_ADDRESS  = 'terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552'
KUJI_SMART_CONTACT_ADDRESS       = 'terra1xfsdgcemqwxp4hhnyk4rle6wr22sseq7j07dnn'
TERRASWAP_UKRW_TO_ULUNA_ADDRESS  = 'terra1erfdlgdtt9e05z0j92wkndwav4t75xzyapntkv'
#TERRASWAP_UKUJI_TO_ULUNA_ADDRESS = 'terra19qx5xe6q9ll4w0890ux7lv2p4mf3csd4qvt3ex'
TERRASWAP_ULUNA_TO_UUSD_ADDRESS = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
BASE_SMART_CONTRACT_ADDRESS = 'terra1uewxz67jhhhs2tj97pfm2egtk7zqxuhenm4y4m'

# Do not change these:

# Standard actions:
USER_ACTION_CLEAR             = 'c'
USER_ACTION_CONTINUE          = 'x'
USER_ACTION_QUIT              = 'q'

# Wallet management constants:
USER_ACTION_ALL               = 'a'
USER_ACTION_DELEGATE          = 'd'
USER_ACTION_SWAP              = 's'
USER_ACTION_SWAP_DELEGATE     = 'sd'
USER_ACTION_WITHDRAW          = 'w'
USER_ACTION_WITHDRAW_DELEGATE = 'wd'

# Validator management constants:
USER_ACTION_VALIDATOR_DELEGATE           = 'd'
USER_ACTION_VALIDATOR_LIST_UNDELEGATIONS = 'l'
USER_ACTION_VALIDATOR_UNDELEGATE         = 'u'
USER_ACTION_VALIDATOR_SWITCH             = 's'

COIN_DIVISOR = 1000000
COIN_DIVISOR_ETH = 1000000000000000000
MAX_VALIDATOR_COUNT = 130

# Coin constants:
UATOM = 'uatom'
UBASE = 'ubase'
UKRW  = 'ukrw'
UKUJI = 'ukuji'
ULUNA = 'uluna'
UOSMO = 'uosmo'
UUSD  = 'uusd'
WETH  = 'weth-wei'

# Coin keys and display values:
FULL_COIN_LOOKUP = {
    'uaud':  'AUT',
    'uatom': 'ATOM',
    'ubase': 'BASE',
    'ucad':  'CAT',
    'uchf':  'CHT',
    'ucny':  'CNT',
    'udkk':  'DKT',
    'ueur':  'EUT',
    'ugbp':  'GBT',
    'uhkd':  'HKT',
    'uidr':  'IDT',
    'uinr':  'INT',
    'ujpy':  'JPT',
    'ukrw':  'KRT',
    'ukuji': 'KUJI',
    'uluna': 'LUNC',
    'umnt':  'MNT',
    'umyr':  'MYT',
    'unok':  'NOT',
    'uosmo': 'OSMO',
    'uphp':  'PHT',
    'usdr':  'SDT',
    'usek':  'SET',
    'usgd':  'SGT',
    'uthb':  'THT',
    'utwd':  'TWT',
    'uusd':  'UST',
    'weth-wei': 'ETH'
}

BASIC_COIN_LOOKUP = {
    'uluna': 'LUNC',
    'uusd':  'UST'
}

# CHAIN_IDS = {
#     #'cosmos': 'channel-2', # Not active
#     #'emoney': 'channel-5', # Not active
#     #'sif': 'channel-7' # Not active
#     #'inj': 'channel-17' # Not active
#     #'axelar': 'channel-19', # Not active
#     #'juno': 'channel-20' # Not active
#     #'umee': 'channel-26', # Not active
#     #'omniflix': 'channel-27', # Not active
#     #'evmos': 'channel-51', # Not active
#     #'gravity': 'channel-64' # Not active
#     #'somm': 'channel-83', # Not active
# }
CHAIN_IDS = {
    'terra': {
        'name': 'terra',
        'name2': 'terra-luna',
        'display_name': 'Luna Classic',
        'chain_id': 'columbus-5',
        'ibc_channels': ['channel-72'],
        'lcd_urls': ['https://lcd.terrarebels.net', 'https://terra-classic-fcd.publicnode.com', 'https://lcd.terrarebels.net', 'https://rest.cosmos.directory/terra'],
        'denom': 'uluna',
        'status': 'active'
    },
    'osmo': {
        'name': 'osmosis',
        'name2': 'osmosis',
        'display_name': 'Osmosis',
        'chain_id': 'osmosis-1',
        'ibc_channels': ['channel-1'],
        'lcd_urls': ['https://lcd.osmosis.zone'],
        'denom': 'uosmo',
        'status': 'active'
    },
    'kujira': {
        'name': 'kujira',
        'name2': 'kujira',
        'display_name': 'Kujira',
        'chain_id': 'kaiyo-1',
        'ibc_channels': ['channel-71'],
        'lcd_urls': ['https://rest.cosmos.directory/kujira', 'https://lcd-kujira.mintthemoon.xyz'],
        'denom': 'ukuji',
        'status': 'active'
    },
    'kava': {
        'name': 'kava',
        'name2': 'kava',
        'display_name': 'Kava',
        'chain_id': 'kava-9',
        'ibc_channels': ['channel-24'],
        'lcd_urls': ['https://rest.cosmos.directory/kava'],
        'denom': 'ukava',
        'status': 'inactive'
    },
    'cosmos': {
        'name': 'cosmos',
        'name2': 'cosmos',
        'display_name': 'Cosmos',
        'chain_id': 'cosmoshub-4',
        'ibc_channels': ['channel-2', 'channel-41', 'channel-59'],
        'lcd_urls': ['https://rest.cosmos.directory/cosmoshub', 'https://cosmoshub-lcd.stakely.io'],
        'denom': 'uatom',
        'status': 'inactive'
    },
    'weth-wei': {
        'name': 'axelar ',
        'name2': 'weth',
        'display_name': 'Wrapped Eth',
        'chain_id': 'axelar-dojo-1',
        #'chain_id': 'osmosis-1',
        'ibc_channels': [],
        'lcd_urls': ['https://rest.cosmos.directory/axelar'],
        #'lcd_urls': ['https://lcd.osmosis.zone'],
        'denom': 'weth-wei',
        'status': 'active'
    }
}

IBC_ADDRESSES = {
    'uluna': {
        'uatom': {
            'token_in': 'ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0',
            'routes': [
                {
                    #"pool_id": "800",
                    "pool_id": "561",
                    "token_out_denom": "uosmo"
                },
                {
                    "pool_id": "1",
                    "token_out_denom": "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"
                }
                # {
                #     "pool_id": "565",
                #     "token_out_denom": "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"
                # },
            ],
            'gas_adjustment': '1.5',
            'fee_multiplier': '1.1'
        },
        'ukuji': {
            'token_in': 'ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0',
            "routes": [
                {
                    "pool_id": "800",
                    "token_out_denom": "uosmo"
                },
                {
                    "pool_id": "744",
                    "token_out_denom": "ibc/BB6BCDB515050BAE97516111873CCD7BCF1FD0CCB723CC12F3C4F704D6C646CE"
                }
            ],
            'gas_adjustment': '1.5',
            'fee_multiplier': '1.1'
        },
        'uosmo': {
            'token_in': 'ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0',
            'routes': [
                {
                    "pool_id": "561",
                    "token_out_denom": "uosmo"
                }
            ],
            'gas_adjustment': '2.5',
            'fee_multiplier': '1'
        },
        'weth-wei': {
            'token_in': 'ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0',
            'routes': [
                {
                    "pool_id": "800",
                    "token_out_denom": "uosmo"
                },
                {
                    #"pool_id": "704",
                    "pool_id": "1134",
                    "token_out_denom": "ibc/EA1D43981D5C9A1C4AAEA9C23BB1D4FA126BA9BC7020A25E0AE4AA841EA25DC5"
                }
            ],
            'gas_adjustment': '2.5',
            'fee_multiplier': '1.1'
        }
    },
    'uosmo': {
        'uluna': {
            'token_in': 'uosmo',
            'routes': [
                {
                    "pool_id": "561",
                    "token_out_denom": "ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0"
                }
            ],
            'gas_adjustment': '2.5',
            'fee_multiplier': '1'
        }
    },
    'uatom': {
        'uluna': {
            'token_in': 'ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2',
            'routes': [
                {
                    "pool_id": "1",
                    "token_out_denom": "uosmo"
                },
                {
                    "pool_id": "800",
                    "token_out_denom": "ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0"
                }
            ],
            'gas_adjustment': '1.5',
            'fee_multiplier': '1.1'
        }
    },
    'ukuji': {
        'uluna': {
            'token_in': 'ibc/BB6BCDB515050BAE97516111873CCD7BCF1FD0CCB723CC12F3C4F704D6C646CE',
            'routes': [
                {
                    "pool_id": "744",
                    "token_out_denom": "uosmo"
                },
                {
                    "pool_id": "800",
                    "token_out_denom": "ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0"
                }
            ],
            'gas_adjustment': '1.5',
            'fee_multiplier': '1.1'
        }
    },
    'weth-wei': {
        'uluna': {
            'token_in': 'ibc/EA1D43981D5C9A1C4AAEA9C23BB1D4FA126BA9BC7020A25E0AE4AA841EA25DC5',
            'routes': [
                {
                    "pool_id": "704",
                    "token_out_denom": "uosmo"
                },
                {
                    "pool_id": "800",
                    "token_out_denom": "ibc/0EF15DF2F02480ADE0BB6E85D9EBB5DAEA2836D3860E9F97F9AADE4F57A31AA0"
                }
            ],
            'gas_adjustment': '2.5',
            'fee_multiplier': '1.1'
        }
    }
}

OSMOSIS_POOLS = {
    '1': {
        'swap_fee': '0.002',
        #'token_in': 'uosmo',
        #'token_out': 'uatom',
        'uosmo': 'uatom',
        'uatom': 'uosmo'
    },
    '561': {
        'swap_fee': '0.002',
        #'token_in': 'uluna',
        #'token_out': 'uosmo',
        'uluna': 'uosmo',
        'uosmo': 'uluna'
    },
    '565': {
        'swap_fee': '0.003',
        'uluna': 'uatom',
        'uatom': 'uluna'
    },
    '704': {
        'swap_fee': '0.002',
        #'token_in': 'uosmo',
        #'token_out': 'weth-wei'
        'uosmo': 'weth-wei',
        'weth-wei': 'uosmo'
    },
    '744': {
        'swap_fee': '0.002',
        #'token_in': 'uosmo',
        #'token_out': 'ukuji'
        'uosmo': 'ukuji',
        'ukuji': 'uosmo'
    },
    '800': {
        'swap_fee': '0.08',
        #'token_in':'uluna',
        #'token_out': 'uosmo'
        'uluna': 'uosmo',
        'uosmo': 'uluna'
    },
    '1134': {
        'swap_fee': '0.002',
        #'token_in':'uluna',
        #'token_out': 'uosmo'
        'uosmo': 'weth-wei',
        'weth-wei': 'uosmo'
    }
}

# Cronos
# Injective
# Kava
# Fetch.ai
# Akash Network
# Band Protocol
# Axelar
# Stride
# Medibloc
# Bluzelle
# Shentu
# Secret
# Evmos
# Sommelier
# Persistence
# IRISnet
# Oraichain
# Cudos
# Stargaze
# KI
# Umee
# Juno
# Cheqd Network
# Ion
# Sentinel
# Carbon Protocol
# Regen
# Mars Protocol
# COMDEX
# Chihuahua Chain
# Lambda
# Planq
# LikeCoin
# Bitsong
# AssetMantle
# Graviton
# Desmos
# IXO
# e-Money
# Decentr
# Odin Protocol
# Starname
# Sifchain
# Vidulum
# Microtick
# Arable Protocol
# Bidao
