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
UATOM = 'uatom'
UBASE = 'ubase'
UKAVA = 'ukava'
UKRW  = 'ukrw'
UKUJI = 'ukuji'
ULUNA = 'uluna'
UOSMO = 'uosmo'
UUSD  = 'uusd'
WETH  = 'weth-wei'

# Coin keys and display values:
FULL_COIN_LOOKUP = {
    'uaud':  'AUTC',
    'uatom': 'ATOM',
    'ubase': 'BASE',
    'ucad':  'CATC',
    'uchf':  'CHTC',
    'ucny':  'CNTC',
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
    'usdr':  'SDTC',
    'usek':  'SETC',
    'usgd':  'SGTC',
    'uthb':  'THTC',
    'utwd':  'TWTC',
    'uusd':  'USTC',
    'weth-wei': 'wETH'
}

BASIC_COIN_LOOKUP = {
    'uluna': 'LUNC',
    'uusd':  'USTC'
}

CHAIN_IDS = {
    'cosmos': {
        'name': 'cosmos',
        'name2': 'cosmos',
        'display_name': 'Cosmos',
        'chain_id': 'cosmoshub-4',
        'ibc_channel': 'channel-0',
        'lcd_urls': ['https://rest.cosmos.directory/cosmoshub', 'https://cosmoshub-lcd.stakely.io'],
        'denom': 'uatom',
        'prefix': 'cosmos'
    },
    'kava': {
        'name': 'kava',
        'name2': 'kava',
        'display_name': 'Kava',
        #'chain_id': 'kava_2222-10',
        'chain_id': 'osmosis-1',
        #'ibc_channel': 'channel-24',
        'ibc_channel': 'channel-143',
        'lcd_urls': ['https://rest.cosmos.directory/kava'],
        'denom': 'ukava',
        'prefix': 'kava'
    },
    'kujira': {
        'name': 'kujira',
        'name2': 'kujira',
        'display_name': 'Kujira',
        'chain_id': 'kaiyo-1',
        'ibc_channel': 'channel-259',
        'lcd_urls': ['https://rest.cosmos.directory/kujira', 'https://lcd-kujira.mintthemoon.xyz'],
        'denom': 'ukuji',
        'prefix': 'kujira'
    },
    'osmo': {
        'name': 'osmosis',
        'name2': 'osmosis',
        'display_name': 'Osmosis',
        'chain_id': 'osmosis-1',
        'ibc_channel': 'channel-1',
        'lcd_urls': ['https://lcd.osmosis.zone'],
        'denom': 'uosmo',
        'prefix': 'osmo'
    },
    'terra': {
        'name': 'terra',
        'name2': 'terra-luna',
        'display_name': 'Luna Classic',
        'chain_id': 'columbus-5',
        'ibc_channel': 'channel-72',
        'lcd_urls': ['https://lcd.terrarebels.net', 'https://terra-classic-fcd.publicnode.com', 'https://lcd.terrarebels.net', 'https://rest.cosmos.directory/terra'],
        'denom': 'uluna',
        'prefix': 'terra'
    },
    'axelar': {
        'name': 'axelar ',
        'name2': 'weth',
        'display_name': 'Wrapped Eth',
        'chain_id': 'axelar-dojo-1',
        'ibc_channel': 'channel-208',
        'lcd_urls': ['https://rest.cosmos.directory/axelar'],
        'denom': 'weth-wei',
        'prefix': 'axelar'
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
