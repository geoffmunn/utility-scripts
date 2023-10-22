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

# Max number of validators that Luna Classic allows
MAX_VALIDATOR_COUNT = 130

# Coin constants:
ACUDOS  = 'acudos'
AEVMOS  = 'aevmos'
AFET    = 'afet'
CRO     = 'basecro'
INJ     = 'inj'
NCHEQ   = 'ncheq'
ORAI    = 'orai'
SWTH    = 'swth'
UAKT    = 'uakt'
UATOM   = 'uatom'
UBAND   = 'uband'
UBASE   = 'ubase'
UBNT    = 'ubnt'
UCTK    = 'uctk'
UDVPN   = 'udvpn'
UHUAHUA = 'uhuahua'
UIRIS   = 'uiris'
UJUNO   = 'ujuno'
UKAVA   = 'ukava'
UKRW    = 'ukrw'
UKUJI   = 'ukuji'
ULUNA   = 'uluna'
UMARS   = 'umars'
UMED    = 'umed'
UMNTL   = 'umntl'
UOSMO   = 'uosmo'
USCRT   = 'uscrt'
USOMM   = 'usomm'
USTARS  = 'ustars'
USTRD   = 'ustrd'
UUMEE   = 'uumee'
UUSD    = 'uusd'
UWHALE  = 'uwhale'
UXKI    = 'uxki'
UXPRT   = 'uxprt'
WBTC    = 'wbtc-satoshi'
WETH    = 'weth-wei'

# Coin keys and display values:
# NOTE: This is in display order, not sorted by key
FULL_COIN_LOOKUP = {
    'uakt':  'Akash',
    'umntl': 'AssetMantle',
    'uaud':  'AUTC',
    'uatom': 'Atom',
    'uband': 'Band Protocol',
    'ubase': 'BASE',
    'ubnt': 'Bluzelle',
    'swth': 'Carbon',
    'ucad':  'CATC',
    'ncheq': 'Cheqd',
    'uchf':  'CHTC',
    'ucny':  'CNTC',
    'basecro': 'CRO',
    'acudos': 'Cudos',
    'udkk':  'DKTC',
    'ueur':  'EUTC',
    'aevmos': 'Evmos',
    'afet': 'Fetch.ai',
    'ugbp':  'GBTC',
    'uhkd':  'HKTC',
    'uhuahua': 'Chihuahua',
    'uidr':  'IDTC',
    'inj': 'Injective',
    'uinr':  'INTC',
    'uiris': 'IRISnet',
    'ujpy':  'JPTC',
    'ujuno': 'Juno',
    'ukava': 'KAVA',
    'uxki': 'Kichain',
    'ukrw':  'KRTC',
    'ukuji': 'KUJI',
    'uluna': 'LUNC',
    'umars': 'Mars Protocol',
    'umed': 'Medibloc',
    'umnt':  'MNTC',
    'umyr':  'MYTC',
    'unok':  'NOTC',
    'orai': 'Oraichain',
    'uosmo': 'OSMO',
    'uxprt': 'Persistance',
    'uphp':  'PHTC',
    'uscrt': 'Secret',
    'usdr':  'SDTC',
    'udvpn': 'Sentinel',
    'usek':  'SETC',
    'usgd':  'SGTC',
    'uctk': 'Shentu',
    'usomm': 'Sommelier',
    'ustars': 'Stargaze',
    'ustrd': 'Stride',
    'uthb':  'THTC',
    'utwd':  'TWTC',
    'uumee': 'Umee',
    'uusd':  'USTC',
    'uwhale': 'Whale',
    'wbtc-satoshi': 'wBTC',
    'weth-wei': 'wETH'
}

BASIC_COIN_LOOKUP = {
    'uluna': 'LUNC',
    'uusd':  'USTC'
}

OFFCHAIN_COINS = [
    ACUDOS,
    AEVMOS,
    AFET,
    UBAND,
    UBNT,
    CRO,
    INJ,
    NCHEQ,
    ORAI,
    SWTH,
    UAKT,
    UATOM,
    UCTK,
    UDVPN,
    UHUAHUA,
    UIRIS,
    UJUNO,
    UKAVA,
    UKUJI,
    UOSMO,
    UMARS,
    UMED,
    UMNTL,
    USCRT,
    USOMM,
    USTARS,
    USTRD,
    UUMEE,
    UUSD,
    UWHALE,
    UXKI,
    UXPRT,
    WBTC,
    WETH
]

# To add a coin to the Osmosis swap options, we need 6 things:
# 1: the denom for this coin, found here: https://cosmos.directory/NAME_HERE/chain
# 2: the cosmos name is listed in the URL: https://cosmos.directory/THIS_NAME/chain
# 3: the Coingecko id, also listed in step 1 or on the Coingecko page for this coin
# 4: the precision, as found here: https://cosmos.directory/cronos/chain (use the correct chain)
# 5: the bech32 prefix, as found here: https://cosmos.directory/cronos/chain (use the correct chain)

# 6: the channel id - found in this result: https://rest.cosmos.directory/osmosis/ibc/apps/transfer/v1/denom_traces/IBC_VALUE_MINUS_IBC
#    To get the IBC value, run this query in osmosis.db: SELECT * FROM asset WHERE readable_denom = 'denom'

###
# 'Step 1': {
#     'cosmos_name': 'Step 2',
#     'keplr_name': 'Step 3',
#     'precision': Step 4,
#     'bech32_prefix': 'Step 5'
# },
#
#'uosmo': {
#        'chain_id': 'osmosis-1',
#        'ibc_channels': {
#            'Step 1': 'Step 6',
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
        'precision': 6,
        'bech32_prefix': 'terra'
    },
    'uosmo': {
        'chain_id': 'osmosis-1',
        'ibc_channels': {
            'acudos': 'channel-298',
            'aevmos': 'channel-204',
            'afet': 'channel-229',
            'basecro': 'channel-5',
            'inj': 'channel-122',
            'ncheq': 'channel-108',
            'orai': 'channel-216',
            'swth': 'channel-188',
            'uakt': 'channel-1',
            'uatom': 'channel-0',
            'uband': 'channel-148',
            'ubnt': 'channel-763',
            'uctk': 'channel-146',
            'udvpn': 'channel-2',
            'uhuahua': 'channel-113',
            'uiris': 'channel-6',
            'ujuno': 'channel-42',
            'ukava': 'channel-143',
            'ukuji': 'channel-259',
            'uluna': 'channel-72',
            'umars': 'channel-557',
            'umed': 'channel-82',
            'umntl': 'channel-232',
            'uumee': 'channel-184',
            'uosmo': 'channel-1',
            'uscrt': 'channel-88',
            'usomm': 'channel-165',
            'ustars': 'channel-75',
            'ustrd': 'channel-326',
            'uusd': 'channel-72',
            'uwhale': 'channel-84',
            'uxki': 'channel-77',
            'uxprt': 'channel-4',
            'wbtc-satoshi': 'channel-208',
            'weth-wei': 'channel-208'
        },
        'lcd_urls': ['https://lcd.osmosis.zone'],
        'coingecko_id': 'osmosis',
        'cosmos_name': 'osmosis',
        'precision': 6,
        'bech32_prefix': 'osmo'
    },
    'acudos': {
        'coingecko_id': 'cudos',
        'cosmos_name': 'cudos',
        'precision': 18,
        'bech32_prefix': 'cudos'
    },
    'aevmos': {
        'coingecko_id': 'evmos',
        'cosmos_name': 'evmos',
        'precision': 18,
        'bech32_prefix': 'evmos'
    },
    'afet': {
        'coingecko_id': 'fetch-ai',
        'cosmos_name': 'fetchhub',
        'precision': 18,
        'bech32_prefix': 'fetch'
    },
    'basecro': {
        'coingecko_id': 'crypto-com-chain',
        'cosmos_name': 'cronos',
        'precision': 8,
        'bech32_prefix': 'cro'
    },
    'inj': {
        'coingecko_id': 'injective-protocol',
        'cosmos_name': 'injective',
        'precision': 18,
        'bech32_prefix': 'inj'
    },
    'ncheq': {
        'coingecko_id': 'cheqd-network',
        'cosmos_name': 'cheqd',
        'precision': 9,
        'bech32_prefix': 'cheqd'
    },
    'orai': {
        'coingecko_id': 'oraichain-token',
        'cosmos_name': 'oraichain',
        'precision': 6,
        'bech32_prefix': 'orai'
    },
    'swth': {
        'coingecko_id': 'switcheo',
        'cosmos_name': 'carbon',
        'precision': 8,
        'bech32_prefix': 'swth'
    },
    'uakt': {
        'coingecko_id': 'akash-network',
        'cosmos_name': 'akash',
        'precision': 6,
        'bech32_prefix': 'akash'
    },
    'uatom': {
        'coingecko_id': 'cosmos',
        'cosmos_name': 'cosmos',
        'precision': 6,
        'bech32_prefix': 'cosmos'
    },
    'uband': {
        'coingecko_id': 'band-protocol',
        'cosmos_name': 'bandchain',
        'precision': 6,
        'bech32_prefix': 'band'
    },
    'ubnt': {
        'coingecko_id': 'bluzelle',
        'cosmos_name': 'bluzelle',
        'precision': 6,
        'bech32_prefix': 'bluzelle'
    },
    'uctk': {
        'coingecko_id': 'certik',
        'cosmos_name': 'shentu',
        'precision': 6,
        'bech32_prefix': 'shentu'
    },
    'udvpn': {
        'coingecko_id': 'sentinel',
        'cosmos_name': 'sentinel',
        'precision': 6,
        'bech32_prefix': 'sent'
    },
    'uhuahua': {
        'coingecko_id': 'chihuahua-token',
        'cosmos_name': 'chihuahua',
        'precision': 6,
        'bech32_prefix': 'chihuahua'
    },
    'uiris': {
        'coingecko_id': 'iris-network',
        'cosmos_name': 'irisnet',
        'precision': 6,
        'bech32_prefix': 'iaa'
    },
    'ujuno': {
        'coingecko_id': 'juno-network',
        'cosmos_name': 'juno',
        'precision': 6,
        'bech32_prefix': 'juno'
    },
    'ukava': {
        'coingecko_id': 'kava',
        'cosmos_name': 'kava',
        'precision': 6,
        'bech32_prefix': 'kava'
    },
    'ukuji': {
        'coingecko_id': 'kujira',
        'cosmos_name': 'kujira',
        'precision': 6,
        'bech32_prefix': 'kujira'
    },
    'umars': {
        'coingecko_id': 'mars-protocol-a7fcbcfb-fd61-4017-92f0-7ee9f9cc6da3',
        'cosmos_name': 'mars',
        'precision': 6,
        'bech32_prefix': 'mars'
    },
    'umed': {
        'coingecko_id': 'medibloc',
        'cosmos_name': 'panacea',
        'precision': 6,
        'bech32_prefix': 'panacea'
    },
    'umntl': {
        'coingecko_id': 'assetmantle',
        'cosmos_name': 'assetmantle',
        'precision': 6,
        'bech32_prefix': 'mantle'
    },
    'uscrt': {
        'coingecko_id': 'secret',
        'cosmos_name': 'secret',
        'precision': 6,
        'bech32_prefix': 'secret'
    },
    'usomm': {
        'coingecko_id': 'sommelier',
        'cosmos_name': 'sommelier',
        'precision': 6,
        'bech32_prefix': 'somm'
    },
    'ustars': {
        'coingecko_id': 'stargaze',
        'cosmos_name': 'stargaze',
        'precision': 6,
        'bech32_prefix': 'stars'
    },
    'ustrd': {
        'coingecko_id': 'stride',
        'cosmos_name': 'stride',
        'precision': 6,
        'bech32_prefix': 'stride'
    },
    'uumee': {
        'coingecko_id': 'umee',
        'cosmos_name': 'umee',
        'precision': 6,
        'bech32_prefix': 'umee'
    },
    'uusd': {
        'coingecko_id': 'terrausd',
        'cosmos_name': 'terra',
        'precision': 6,
        'bech32_prefix': 'terra'
    },
    'uwhale': {
        'coingecko_id': 'white-whale',
        'cosmos_name': 'whale',
        'precision': 6,
        'bech32_prefix': 'migaloo'
    },
    'uxki': {
        'coingecko_id': 'ki',
        'cosmos_name': 'kichain',
        'precision': 6,
        'bech32_prefix': 'ki'
    },
    'uxprt': {
        'coingecko_id': 'persistence',
        'cosmos_name': 'persistence',
        'precision': 6,
        'bech32_prefix': 'persistence'
    },
    'wbtc-satoshi': {
        'coingecko_id': 'bitcoin',
        'cosmos_name': 'axelar',
        'precision': 8,
        'bech32_prefix': 'axelar'
    },
    'weth-wei': {
        'coingecko_id': 'ethereum',
        'cosmos_name': 'axelar',
        'precision': 18,
        'bech32_prefix': 'axelar'
    }
}

# Carbon Protocol
# Regen
# COMDEX
# Lambda
# Planq
# LikeCoin
# Bitsong
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
# Bidao
