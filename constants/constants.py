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
ACUDOS    = 'acudos'
AEVMOS    = 'aevmos'
AFET      = 'afet'
APLANQ    = 'aplanq'
BASECRO   = 'basecro'
INJ       = 'inj'
LOKI      = 'loki'
NANOLIKE  = 'nanolike'
NCHEQ     = 'ncheq'
ORAI      = 'orai'
SWTH      = 'swth'
UAKT      = 'uakt'
UATOM     = 'uatom'
UBAND     = 'uband'
UBASE     = 'ubase'
UBNT      = 'ubnt'
UBTSG     = 'ubtsg'
UCMDX     = 'ucmdx'
UCTK      = 'uctk'
UDEC      = 'udec'
UDSM      = 'udsm'
UDVPN     = 'udvpn'
UGRAVITON = 'ugraviton'
UHUAHUA   = 'uhuahua'
UIRIS     = 'uiris'
UIXO      = 'uixo'
UJUNO     = 'ujuno'
UKAVA     = 'ukava'
UKRW      = 'ukrw'
UKUJI     = 'ukuji'
ULAMB     = 'ulamb'
ULUNA     = 'uluna'
UMARS     = 'umars'
UMED      = 'umed'
UMNTL     = 'umntl'
UNGM      = 'ungm'
UOSMO     = 'uosmo'
UREGEN    = 'uregen'
USCRT     = 'uscrt'
USOMM     = 'usomm'
USTARS    = 'ustars'
USTRD     = 'ustrd'
UUMEE     = 'uumee'
UUSD      = 'uusd'
UWHALE    = 'uwhale'
UXKI      = 'uxki'
UXPRT     = 'uxprt'
WBTC      = 'wbtc-satoshi'
WETH      = 'weth-wei'

# Coin keys and display values:
# NOTE: This is in display order, not sorted by key
FULL_COIN_LOOKUP = {
    UAKT:      'Akash',
    UMNTL:     'AssetMantle',
    'uaud':    'AUTC',
    UATOM:     'Atom',
    UBAND:     'Band Protocol',
    UBASE:     'BASE',
    UBTSG:     'Bitsong',
    UBNT:      'Bluzelle',
    SWTH:      'Carbon',
    'ucad':    'CATC',
    NCHEQ:     'Cheqd',
    UHUAHUA:   'Chihuahua',
    'uchf':    'CHTC',
    UCMDX:     'Comdex',
    'ucny':    'CNTC',
    BASECRO:   'CRO',
    ACUDOS:    'Cudos',
    UDEC:      'Decentr',
    UDSM:      'Desmos',
    'udkk':    'DKTC',
    UNGM:      'e-Money',
    'ueur':    'EUTC',
    AEVMOS:    'Evmos',
    AFET:      'Fetch.ai',
    'ugbp':    'GBTC',
    UGRAVITON: 'Gravity Bridge',
    'uhkd':    'HKTC',
    'uidr':    'IDTC',
    INJ:       'Injective',
    'uinr':    'INTC',
    UIRIS:     'IRISnet',
    UIXO:      'Ixo Protocol',
    'ujpy':    'JPTC',
    UJUNO:     'Juno',
    UKAVA:     'KAVA',
    UXKI:      'Kichain',
    'ukrw':    'KRTC',
    UKUJI:     'KUJI',
    ULAMB:     'Lambda',
    NANOLIKE:  'Likecoin',
    ULUNA:     'LUNC',
    UMARS:     'Mars Protocol',
    UMED:      'Medibloc',
    'umnt':    'MNTC',
    'umyr':    'MYTC',
    'unok':    'NOTC',
    LOKI:      'Odin protocol',
    ORAI:      'Oraichain',
    UOSMO:     'OSMO',
    UXPRT:     'Persistance',
    'uphp':    'PHTC',
    APLANQ:    'Planq',
    UREGEN:    'Regen',
    USCRT:     'Secret',
    'usdr':    'SDTC',
    UDVPN:     'Sentinel',
    'usek':    'SETC',
    'usgd':    'SGTC',
    UCTK:      'Shentu',
    USOMM:     'Sommelier',
    USTARS:    'Stargaze',
    USTRD:     'Stride',
    'uthb':    'THTC',
    'utwd':    'TWTC',
    UUMEE:     'Umee',
    UUSD:      'USTC',
    UWHALE:    'Whale',
    WBTC:      'wBTC',
    WETH:      'wETH'
}

BASIC_COIN_LOOKUP = {
    ULUNA: 'LUNC',
    UUSD:  'USTC'
}

# OFFCHAIN_COINS_old = [
#     ACUDOS,
#     AEVMOS,
#     AFET,
#     APLANQ,
#     UBAND,
#     UBNT,
#     BASECRO,
#     INJ,
#     NANOLIKE,
#     NCHEQ,
#     ORAI,
#     SWTH,
#     UAKT,
#     UATOM,
#     UCMDX,
#     UCTK,
#     UDVPN,
#     UHUAHUA,
#     UIRIS,
#     UJUNO,
#     UKAVA,
#     UKUJI,
#     ULAMB,
#     UOSMO,
#     UMARS,
#     UMED,
#     UMNTL,
#     UREGEN,
#     USCRT,
#     USOMM,
#     USTARS,
#     USTRD,
#     UUMEE,
#     UUSD,
#     UWHALE,
#     UXKI,
#     UXPRT,
#     WBTC,
#     WETH
# ]

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
    ULUNA: {
        'chain_id':      'columbus-5',
        'ibc_channels':  {
            'uosmo': 'channel-1',
        },
        'lcd_urls':      ['https://terra-classic-fcd.publicnode.com', 'https://rest.cosmos.directory/terra'],
        'coingecko_id':  'terra-luna',
        'cosmos_name':   'terra',
        'precision':     6,
        'bech32_prefix': 'terra'
    },
    UOSMO: {
        'chain_id':      'osmosis-1',
        'ibc_channels':  {
            ACUDOS:    'channel-298',
            AEVMOS:    'channel-204',
            AFET:      'channel-229',
            APLANQ:    'channel-492',
            BASECRO:   'channel-5',
            INJ:       'channel-122',
            LOKI:      'channel-258',
            NANOLIKE:  'channel-53',
            NCHEQ:     'channel-108',
            ORAI:      'channel-216',
            SWTH:      'channel-188',
            UAKT:      'channel-1',
            UATOM:     'channel-0',
            UBAND:     'channel-148',
            UBNT:      'channel-763',
            UBTSG:     'channel-73',
            UCMDX:     'channel-87',
            UCTK:      'channel-146',
            UDEC:      'channel-181',
            UDSM:      'channel-135',
            UDVPN:     'channel-2',
            UGRAVITON: 'channel-144',
            UHUAHUA:   'channel-113',
            UIRIS:     'channel-6',
            UIXO:      'channel-38',
            UJUNO:     'channel-42',
            UKAVA:     'channel-143',
            UKUJI:     'channel-259',
            ULAMB:     'channel-378',
            ULUNA:     'channel-72',
            UMARS:     'channel-557',
            UMED:      'channel-82',
            UMNTL:     'channel-232',
            UNGM:      'channel-37',
            UOSMO:     'channel-1',
            UREGEN:    'channel-8',
            USCRT:     'channel-88',
            USOMM:     'channel-165',
            USTARS:    'channel-75',
            USTRD:     'channel-326',
            UUMEE:     'channel-184',
            UUSD:      'channel-72',
            UWHALE:    'channel-84',
            UXKI:      'channel-77',
            UXPRT:     'channel-4',
            WBTC:      'channel-208',
            WETH:      'channel-208'
        },
        'lcd_urls':      ['https://lcd.osmosis.zone'],
        'coingecko_id':  'osmosis',
        'cosmos_name':   'osmosis',
        'precision':     6,
        'bech32_prefix': 'osmo'
    },
    ACUDOS: {
        'coingecko_id':  'cudos',
        'cosmos_name':   'cudos',
        'precision':     18,
        'bech32_prefix': 'cudos'
    },
    AEVMOS: {
        'coingecko_id':  'evmos',
        'cosmos_name':   'evmos',
        'precision':     18,
        'bech32_prefix': 'evmos'
    },
    AFET: {
        'coingecko_id':  'fetch-ai',
        'cosmos_name':   'fetchhub',
        'precision':     18,
        'bech32_prefix': 'fetch'
    },
    APLANQ: {
        'coingecko_id':  'planq',
        'cosmos_name':   'planq',
        'precision':     18,
        'bech32_prefix': 'plq'
    },
    BASECRO: {
        'coingecko_id':  'crypto-com-chain',
        'cosmos_name':   'cronos',
        'precision':     8,
        'bech32_prefix': 'cro'
    },
    INJ: {
        'coingecko_id':  'injective-protocol',
        'cosmos_name':   'injective',
        'precision':     18,
        'bech32_prefix': 'inj'
    },
    LOKI: {
        'coingecko_id':  'odin-protocol',
        'cosmos_name':   'odin',
        'precision':     6,
        'bech32_prefix': 'odin'
    },
    NANOLIKE: {
        'coingecko_id':  'likecoin',
        'cosmos_name':   'likecoin',
        'precision':     9,
        'bech32_prefix': 'like'
    },
    NCHEQ: {
        'coingecko_id':  'cheqd-network',
        'cosmos_name':   'cheqd',
        'precision':     9,
        'bech32_prefix': 'cheqd'
    },
    ORAI: {
        'coingecko_id':  'oraichain-token',
        'cosmos_name':   'oraichain',
        'precision':     6,
        'bech32_prefix': 'orai'
    },
    SWTH: {
        'coingecko_id':  'switcheo',
        'cosmos_name':   'carbon',
        'precision':     8,
        'bech32_prefix': 'swth'
    },
    UAKT: {
        'coingecko_id':  'akash-network',
        'cosmos_name':   'akash',
        'precision':     6,
        'bech32_prefix': 'akash'
    },
    UATOM: {
        'coingecko_id':  'cosmos',
        'cosmos_name':   'cosmos',
        'precision':     6,
        'bech32_prefix': 'cosmos'
    },
    UBAND: {
        'coingecko_id':  'band-protocol',
        'cosmos_name':   'bandchain',
        'precision':     6,
        'bech32_prefix': 'band'
    },
    UBNT: {
        'coingecko_id':  'bluzelle',
        'cosmos_name':   'bluzelle',
        'precision':     6,
        'bech32_prefix': 'bluzelle'
    },
    UBTSG: {
        'coingecko_id':  'bitsong',
        'cosmos_name':   'bitsong',
        'precision':     6,
        'bech32_prefix': 'bitsong'
    },
    UCMDX: {
        'coingecko_id':  'comdex',
        'cosmos_name':   'comdex',
        'precision':     6,
        'bech32_prefix': 'comdex'
    },
    UCTK: {
        'coingecko_id':  'certik',
        'cosmos_name':   'shentu',
        'precision':     6,
        'bech32_prefix': 'shentu'
    },
    UDEC: {
        'coingecko_id':  'decentr',
        'cosmos_name':   'decentr',
        'precision':     6,
        'bech32_prefix': 'decentr'
    },
    UDSM: {
        'coingecko_id':  'desmos',
        'cosmos_name':   'desmos',
        'precision':     6,
        'bech32_prefix': 'desmos'
    },
    UDVPN: {
        'coingecko_id':  'sentinel',
        'cosmos_name':   'sentinel',
        'precision':     6,
        'bech32_prefix': 'sent'
    },
    UGRAVITON: {
        'coingecko_id':  'graviton',
        'cosmos_name':   'gravitybridge',
        'precision':     6,
        'bech32_prefix': 'gravity'
    },
    UHUAHUA: {
        'coingecko_id':  'chihuahua-token',
        'cosmos_name':   'chihuahua',
        'precision':     6,
        'bech32_prefix': 'chihuahua'
    },
    UIRIS: {
        'coingecko_id':  'iris-network',
        'cosmos_name':   'irisnet',
        'precision':     6,
        'bech32_prefix': 'iaa'
    },
    UIXO: {
        'coingecko_id':  'ixo',
        'cosmos_name':   'impacthub',
        'precision':     6,
        'bech32_prefix': 'ixo'
    },
    UJUNO: {
        'coingecko_id':  'juno-network',
        'cosmos_name':   'juno',
        'precision':     6,
        'bech32_prefix': 'juno'
    },
    UKAVA: {
        'coingecko_id':  'kava',
        'cosmos_name':   'kava',
        'precision':     6,
        'bech32_prefix': 'kava'
    },
    UKUJI: {
        'coingecko_id':  'kujira',
        'cosmos_name':   'kujira',
        'precision':     6,
        'bech32_prefix': 'kujira'
    },
    ULAMB: {
        'coingecko_id':  'lambda',
        'cosmos_name':   'lambda',
        'precision':     18,
        'bech32_prefix': 'lamb'
    },
    UMARS: {
        'coingecko_id':  'mars-protocol-a7fcbcfb-fd61-4017-92f0-7ee9f9cc6da3',
        'cosmos_name':   'mars',
        'precision':     6,
        'bech32_prefix': 'mars'
    },
    UMED: {
        'coingecko_id':  'medibloc',
        'cosmos_name':   'panacea',
        'precision':     6,
        'bech32_prefix': 'panacea'
    },
    UMNTL: {
        'coingecko_id':  'assetmantle',
        'cosmos_name':   'assetmantle',
        'precision':     6,
        'bech32_prefix': 'mantle'
    },
    UNGM: {
        'coingecko_id':  'e-money',
        'cosmos_name':   'emoney',
        'precision':     6,
        'bech32_prefix': 'emoney'
    },
    UREGEN: {
        'coingecko_id':  'regen',
        'cosmos_name':   'regen',
        'precision':     6,
        'bech32_prefix': 'regen'
    },
    USCRT: {
        'coingecko_id':  'secret',
        'cosmos_name':   'secret',
        'precision':     6,
        'bech32_prefix': 'secret'
    },
    USOMM: {
        'coingecko_id':  'sommelier',
        'cosmos_name':   'sommelier',
        'precision':     6,
        'bech32_prefix': 'somm'
    },
    USTARS: {
        'coingecko_id':  'stargaze',
        'cosmos_name':   'stargaze',
        'precision':     6,
        'bech32_prefix': 'stars'
    },
    USTRD: {
        'coingecko_id':  'stride',
        'cosmos_name':   'stride',
        'precision':     6,
        'bech32_prefix': 'stride'
    },
    UUMEE: {
        'coingecko_id':  'umee',
        'cosmos_name':   'umee',
        'precision':     6,
        'bech32_prefix': 'umee'
    },
    UUSD: {
        'coingecko_id':  'terrausd',
        'cosmos_name':   'terra',
        'precision':     6,
        'bech32_prefix': 'terra'
    },
    UWHALE: {
        'coingecko_id':  'white-whale',
        'cosmos_name':   'whale',
        'precision':     6,
        'bech32_prefix': 'migaloo'
    },
    UXKI: {
        'coingecko_id':  'ki',
        'cosmos_name':   'kichain',
        'precision':     6,
        'bech32_prefix': 'ki'
    },
    UXPRT: {
        'coingecko_id':  'persistence',
        'cosmos_name':   'persistence',
        'precision':     6,
        'bech32_prefix': 'persistence'
    },
    WBTC: {
        'coingecko_id':  'bitcoin',
        'cosmos_name':   'axelar',
        'precision':     8,
        'bech32_prefix': 'axelar'
    },
    WETH: {
        'coingecko_id':  'ethereum',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    }
}

OFFCHAIN_COINS = []
for item in CHAIN_DATA[UOSMO]['ibc_channels'].keys():
    if item != ULUNA:
        OFFCHAIN_COINS.append(item)

# Odin Protocol
# Starname
# Sifchain
# Vidulum
# Microtick
# Bidao
