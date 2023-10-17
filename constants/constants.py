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
MIN_OSMO_GAS             = 0.0025

# Swap contracts can be found here
# https://assets.terra.money/cw20/pairs.dex.json
TERRASWAP_UUSD_TO_ULUNA_ADDRESS = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
#TERRASWAP_UKRW_TO_UUSD_ADDRESS  = 'terra1untf85jwv3kt0puyyc39myxjvplagr3wstgs5s'
#ASTROPORT_UUSD_TO_MINA_ADDRESS  = 'terra134m8n2epp0n40qr08qsvvrzycn2zq4zcpmue48'
#ASTROPORT_UUSD_TO_UKUJI_ADDRESS  = 'terra1hasy32pvxmgu485x5tujylemqxynsv72lsu7ve'
#ASTROPORT_UUSD_TO_ULUNA_ADDRESS  = 'terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552'
KUJI_SMART_CONTACT_ADDRESS      = 'terra1xfsdgcemqwxp4hhnyk4rle6wr22sseq7j07dnn'
TERRASWAP_UKRW_TO_ULUNA_ADDRESS = 'terra1erfdlgdtt9e05z0j92wkndwav4t75xzyapntkv'
#TERRASWAP_UKUJI_TO_ULUNA_ADDRESS = 'terra19qx5xe6q9ll4w0890ux7lv2p4mf3csd4qvt3ex'
TERRASWAP_ULUNA_TO_UUSD_ADDRESS = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
BASE_SMART_CONTRACT_ADDRESS     = 'terra1uewxz67jhhhs2tj97pfm2egtk7zqxuhenm4y4m'

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

# Precision values
COIN_DIVISOR        = 1000000

# Max number of validators that Luna Classic allows
MAX_VALIDATOR_COUNT = 130

# Coin constants:
CRO   = 'basecro'
UATOM = 'uatom'
UBASE = 'ubase'
UKAVA = 'ukava'
UKRW  = 'ukrw'
UKUJI = 'ukuji'
ULUNA = 'uluna'
UMARS = 'umars'
UOSMO = 'uosmo'
USCRT = 'uscrt'
UUSD  = 'uusd'
UUSTC = 'uusdc'
UWHALE = 'uwhale'
WBTC  = 'wbtc-satoshi'
WETH  = 'weth-wei'

# Coin keys and display values:
FULL_COIN_LOOKUP = {
    'uaud':  'AUTC',
    'uatom': 'ATOM',
    'ubase': 'BASE',
    'ucad':  'CATC',
    'uchf':  'CHTC',
    'ucny':  'CNTC',
    'basecro': 'CRO',
    'udkk':  'DKTC',
    'ueur':  'EUTC',
    'ugbp':  'GBTC',
    'uhkd':  'HKTC',
    'uidr':  'IDTC',
    'uinr':  'INTC',
    'ujpy':  'JPTC',
    'ukava': 'KAVA',
    'ukrw':  'KRTC',
    'ukuji': 'KUJI',
    'uluna': 'LUNC',
    'umars': 'MARS',
    'umnt':  'MNTC',
    'umyr':  'MYTC',
    'unok':  'NOTC',
    'uosmo': 'OSMO',
    'uphp':  'PHTC',
    'uscrt': 'SCRT',
    'usdr':  'SDTC',
    'usek':  'SETC',
    'usgd':  'SGTC',
    'uthb':  'THTC',
    'utwd':  'TWTC',
    'uusd':  'USTC',
    'uwhale': 'WHALE',
    'wbtc-satoshi': 'wBTC',
    'weth-wei': 'wETH'
}

BASIC_COIN_LOOKUP = {
    'uluna': 'LUNC',
    'uusd':  'USTC'
}

OFFCHAIN_COINS = [
    CRO,
    UATOM,
    UKAVA,
    UKUJI,
    UOSMO,
    UMARS,
    USCRT,
    UUSD,
    UWHALE,
    WBTC,
    WETH
]

# To add a coin to the Osmosis swap options, we need 5 things:
# 1: the denom for this coin, found here: https://cosmos.directory/cronos/chain
# 2: the cosmos name that goes into this url: https://rest.cosmos.directory/osmosis/ibc/apps/transfer/v1/denom_traces/IBC_VALUE_MINUS_IBC
#    To get the IBC value, run this query in osmosis.db: SELECT * FROM asset WHERE readable_denom = 'denom'
# 3: the keplr name, that goes into this url: https://api-indexer.keplr.app/v1/price?ids=terra-luna,KEPLR_NAME&vs_currencies=usd
# 4: the precision, as found here: https://cosmos.directory/cronos/chain (use the correct chain)
# 5: the bech32 prefix, as found here: https://cosmos.directory/cronos/chain (use the correct chain)

# 6: the channel id (also found in step 1)
###
# 'Step 1': {
#     'cosmos_name': 'Step 2',
#     'keplr_name': 'Step 3',
#     'precision': Step 4,
#     'bech32_prefix': 'Step 5'
# },
###
CHAIN_DATA = {
    'uluna': {
        'chain_id': 'columbus-5',
        'ibc_channels': {
            'uosmo': 'channel-1',
        },
        'lcd_urls': ['https://terra-classic-fcd.publicnode.com', 'https://rest.cosmos.directory/terra'],
        'coingecko_id': 'terra-luna',
        'cosmos_name': 'terra',
        'keplr_name': 'terra-luna',
        'precision': 6,
        'bech32_prefix': 'terra'
    },
    'uosmo': {
        'chain_id': 'osmosis-1',
        'ibc_channels': {
            'basecro': 'channel-5',
            'uatom': 'channel-0',
            'ukava': 'channel-143',
            'ukuji': 'channel-259',
            'uluna': 'channel-72',
            'umars': 'channel-557',
            'uosmo': 'channel-1',
            'uscrt': 'channel-88',
            'uusd': 'channel-72',
            'uwhale': 'channel-84',
            'wbtc-satoshi': 'channel-208',
            'weth-wei': 'channel-208'
        },
        'lcd_urls': ['https://lcd.osmosis.zone'],
        'coingecko_id': 'osmosis',
        'cosmos_name': 'osmosis',
        'keplr_name': 'osmosis',
        'precision': 6,
        'bech32_prefix': 'osmo'
    },
    'basecro': {
        'coingecko_id': 'crypto-com-chain',
        'cosmos_name': 'cronos',
        'keplr_name': 'cronos',
        'precision': 8,
        'bech32_prefix': 'basecro'
    },
    'uatom': {
        'coingecko_id': 'cosmos',
        'cosmos_name': 'cosmos',
        'keplr_name': 'cosmos',
        'precision': 6,
        'bech32_prefix': 'cosmos'
    },
    'ukava': {
        'coingecko_id': 'kava',
        'cosmos_name': 'kava',
        'keplr_name': 'kava',
        'precision': 6,
        'bech32_prefix': 'kava'
    },
    'ukuji': {
        'coingecko_id': 'kujira',
        'cosmos_name': 'kujira',
        'keplr_name': 'kujira',
        'precision': 6,
        'bech32_prefix': 'kujira'
    },
    'umars': {
        'coingecko_id': 'mars-protocol-a7fcbcfb-fd61-4017-92f0-7ee9f9cc6da3',
        'cosmos_name': 'mars',
        'keplr_name': 'mars',
        'precision': 6,
        'bech32_prefix': 'mars'
    },
    'uscrt': {
        'coingecko_id': 'secret',
        'cosmos_name': 'secret',
        'keplr_name': 'secret',
        'precision': 6,
        'bech32_prefix': 'secret'
    },
    'uusd': {
        'coingecko_id': 'terrausd',
        'cosmos_name': 'terra',
        'keplr_name': 'terrausd',
        'precision': 6,
        'bech32_prefix': 'terra'
    },
    'uwhale': {
        'coingecko_id': 'white-whale',
        'cosmos_name': 'whale',
        'keplr_name': 'whale',
        'precision': 6,
        'bech32_prefix': 'migaloo'
    },
    'wbtc-satoshi': {
        'coingecko_id': 'bitcoin',
        'cosmos_name': 'axelar',
        'keplr_name': 'bitcoin',
        'precision': 8,
        'bech32_prefix': 'axelar'
    },
    'weth-wei': {
        'coingecko_id': 'ethereum',
        'cosmos_name': 'axelar',
        'keplr_name': 'weth',
        'precision': 18,
        'bech32_prefix': 'axelar'
    }
}

# CHAIN_IDS = {
#     'secret': {
#         'chain_id': 'osmosis-1',
#         #'chain_id': 'secret-4',
#         'denom': 'uscrt',
#         'display_name': 'Luna Classic',
#         'ibc_channel': 'channel-88',
#         'lcd_urls': ['https://lcd.osmosis.zone'],
#         #'lcd_urls': ['https://lcd.secret.express'],
#         'name': 'secret',
#         'name2': 'secret',
#         'precision': 6,
#         'prefix': 'secret'
#     },
# }

# Injective
# Fetch.ai
# Akash Network
# Band Protocol
# Stride
# Medibloc
# Bluzelle
# Shentu
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
