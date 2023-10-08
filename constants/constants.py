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
COIN_DIVISOR_ETH    = 1000000000000000000

# Max number of validators that Luna Classic allows
MAX_VALIDATOR_COUNT = 130

# Coin constants:
#CRO   = 'cro'
UATOM = 'uatom'
UBASE = 'ubase'
UKAVA = 'ukava'
UKRW  = 'ukrw'
UKUJI = 'ukuji'
ULUNA = 'uluna'
UOSMO = 'uosmo'
USCRT = 'uscrt'
UUSD  = 'uusd'
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
    #'cro': 'CRO',
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
    'umnt':  'MNTC',
    'umyr':  'MYTC',
    'unok':  'NOTC',
    'uosmo': 'OSMO',
    'uphp':  'PHTC',
    #'uscrt': 'SCRT',
    'usdr':  'SDTC',
    'usek':  'SETC',
    'usgd':  'SGTC',
    'uthb':  'THTC',
    'utwd':  'TWTC',
    'uusd':  'USTC',
    #'uwhale': 'WHALE',
    'wbtc-satoshi': 'wBTC',
    'weth-wei': 'wETH'
}

BASIC_COIN_LOOKUP = {
    'uluna': 'LUNC',
    'uusd':  'USTC'
}

OFFCHAIN_COINS = [
    #CRO,
    UATOM,
    UKAVA,
    UKUJI,
    UOSMO,
    USCRT,
    UWHALE,
    WBTC,
    WETH
]

CHAIN_DATA = {
    # 'uatom': {
    #     'chain_id': 'cosmoshub-4',
    #     'ibc_channel': 'channel-0',
    #     'lcd_urls': ['https://rest.cosmos.directory/cosmoshub', 'https://cosmoshub-lcd.stakely.io'],
    #     'name': 'cosmos',
    #     'keplr_name': 'cosmos',
    #     'precision': 6,
    #     'prefix': 'cosmos'
    # },
    # 'ukava': {
    #     'chain_id': 'osmosis-1',
    #     'ibc_channel': 'channel-143',
    #     'lcd_urls': ['https://rest.cosmos.directory/kava'],
    #     'name': 'kava',
    #     'keplr_name': 'kava',
    #     'precision': 6,
    #     'prefix': 'kava'
    # },
    # 'ukuji': {
    #     'chain_id': 'kaiyo-1',
    #     'ibc_channel': 'channel-259',
    #     'lcd_urls': ['https://rest.cosmos.directory/kujira', 'https://lcd-kujira.mintthemoon.xyz'],
    #     'name': 'kujira',
    #     'keplr_name': 'kujira',
    #     'precision': 6,
    #     'prefix': 'kujira'
    # },
    'uluna': {
        'chain_id': 'columbus-5',
        'ibc_channels': {
            'uluna': 'channel-1',
        },
        'lcd_urls': ['https://terra-classic-fcd.publicnode.com', 'https://rest.cosmos.directory/terra'],
        'name': 'terra',
        'keplr_name': 'terra-luna',
        'precision': 6,
        'prefix': 'terra'
    },
    'uosmo': {
        'chain_id': 'osmosis-1',
        #'ibc_channel': 'channel-72',
        'ibc_channels': {
            'uluna': 'channel-72',
            'weth-wei': 'channel-208'
        },
        'lcd_urls': ['https://lcd.osmosis.zone'],
        'name': 'osmosis',
        'keplr_name': 'osmosis',
        'precision': 6,
        'prefix': 'osmo'
    },
    # 'uusd': {
    #     'chain_id': 'columbus-5',
    #     'ibc_channel': 'channel-72',
    #     'lcd_urls': ['https://lcd.terraclassic.community/', 'https://terra-classic-fcd.publicnode.com', 'https://lcd.terraclassic.community/', 'https://rest.cosmos.directory/terra'],
    #     'name': 'terra',
    #     'keplr_name': 'terra-luna',
    #     'precision': 6,
    #     'prefix': 'terra'
    # },
    # 'wbtc-satoshi': {
    #     #'chain_id': 'axelar-dojo-1',
    #     'chain_id': 'osmosis-1',
    #     'ibc_channel': 'channel-208',
    #     #'lcd_urls': ['https://rest.cosmos.directory/axelar'],
    #     'lcd_urls': ['https://lcd.osmosis.zone'],
    #     'name': 'axelar',
    #     'keplr_name': 'bitcoin',
    #     'precision': 8,
    #     'prefix': 'axelar'
    # },
    'weth-wei': {
        'chain_id': 'axelar-dojo-1',
        'ibc_channel': 'channel-208',
        'lcd_urls': ['https://rest.cosmos.directory/axelar'],
        'name': 'axelar',
        'keplr_name': 'weth',
        'precision': 18,
        'prefix': 'axelar'
    }
}

# CHAIN_IDS = {
#     'axelar': {
#         'chain_id': 'axelar-dojo-1',
#         'denom': 'weth-wei',
#         'display_name': 'Wrapped Eth',
#         'ibc_channel': 'channel-208',
#         'lcd_urls': ['https://rest.cosmos.directory/axelar'],
#         'name': 'axelar ',
#         'name2': 'weth',
#         'precision': 18,
#         'prefix': 'axelar'
#     },
#     'cosmos': {
#         'chain_id': 'cosmoshub-4',
#         'denom': 'uatom',
#         'display_name': 'Cosmos',
#         'ibc_channel': 'channel-0',
#         'lcd_urls': ['https://rest.cosmos.directory/cosmoshub', 'https://cosmoshub-lcd.stakely.io'],
#         'name': 'cosmos',
#         'name2': 'cosmos',
#         'precision': 6,
#         'prefix': 'cosmos'
#     },
#     # 'cro': {
#     #     'chain_id': 'osmosis-1',
#     #     'denom': 'cro',
#     #     'display_name': 'Cronos',
#     #     'ibc_channel': '',
#     #     'lcd_urls': ['rest.cosmos.directory/cronos'],
#     #     'name': 'cronos',
#     #     'name2': 'cronos',
#     #     'precision': 18
#     # },
#     'kava': {
#         'chain_id': 'osmosis-1',
#         'denom': 'ukava',
#         'display_name': 'Kava',
#         'ibc_channel': 'channel-143',
#         'lcd_urls': ['https://rest.cosmos.directory/kava'],
#         'name': 'kava',
#         'name2': 'kava',
#         'precision': 6,
#         'prefix': 'kava'
#     },
#     'kujira': {
#         'chain_id': 'kaiyo-1',
#         'denom': 'ukuji',
#         'display_name': 'Kujira',
#         'ibc_channel': 'channel-259',
#         'lcd_urls': ['https://rest.cosmos.directory/kujira', 'https://lcd-kujira.mintthemoon.xyz'],
#         'name': 'kujira',
#         'name2': 'kujira',
#         'precision': 6,
#         'prefix': 'kujira'
#     },
#     'osmo': {
#         'chain_id': 'osmosis-1',
#         'denom': 'uosmo',
#         'display_name': 'Osmosis',
#         'ibc_channel': 'channel-1',
#         'lcd_urls': ['https://lcd.osmosis.zone'],
#         'name': 'osmosis',
#         'name2': 'osmosis',
#         'precision': 6,
#         'prefix': 'osmo'
#     },
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
#     'terra': {
#         'chain_id': 'columbus-5',
#         'denom': 'uluna',
#         'display_name': 'Luna Classic',
#         'ibc_channel': 'channel-72',
#         'lcd_urls': ['https://terra-classic-fcd.publicnode.com', 'https://lcd.terrarebels.net', 'https://rest.cosmos.directory/terra'],
#         'name': 'terra',
#         'name2': 'terra-luna',
#         'precision': 6,
#         'prefix': 'terra'
#     },
#     'whale': {
#         'chain_id': 'osmosis-1',
#         'denom': 'uwhale',
#         'display_name': 'White Whale',
#         'ibc_channel': 'channel-84',
#         'lcd_urls': ['https://rest.cosmos.directory/migaloo', 'https://lcd.osmosis.zone'],
#         'name': 'whale',
#         'name2': 'whale',
#         'precision': 6,
#         'prefix': 'migaloo'
#     }
# }

# Cronos
# Injective
# Fetch.ai
# Akash Network
# Band Protocol
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
