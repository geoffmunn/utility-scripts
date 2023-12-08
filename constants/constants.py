#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# User settings - can be changed if required
CHECK_FOR_UPDATES    = True
WITHDRAWAL_REMAINDER = 250   # This is the amount of Lunc we want to keep after withdrawal and before delegating. You should never delegate the entire balance.
SEARCH_RETRY_COUNT   = 30    # This is the number of times we will check for a transaction to appear in the chain before deciding it didn't work.
HIDE_DISABLED_COINS  = True  # Some coins are not currently available. Functionality is mostly there, but swaps etc won't work

# System settings - these can be changed, but shouldn't be necessary
GAS_PRICE_URI            = 'https://terra-classic-fcd.publicnode.com/v1/txs/gas_prices'
#GAS_PRICE_URI            = 'https://rest.cosmos.directory/terra/v1/txs/gas_prices'
TOKEN_LIST               = 'https://assets.terrarebels.net/cw20/tokens.json'

# File names:
CONFIG_FILE_NAME         = 'user_config.yml'
DB_FILE_NAME             = 'osmosis.db'
VERSION_URI              = 'https://raw.githubusercontent.com/geoffmunn/utility-scripts/main/version.json'

# Gas adjustments and other values
GAS_ADJUSTMENT           = 3.6
GAS_ADJUSTMENT_SEND      = 3.6
GAS_ADJUSTMENT_SWAPS     = 3.6
GAS_ADJUSTMENT_OSMOSIS   = 1.5
MIN_OSMO_GAS             = 0.0025
OSMOSIS_FEE_MULTIPLIER   = 1.5

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

# Create wallet constants:
CHAIN_TERRA = 't'
CHAIN_OSMO  = 'o'

# Validator management constants:
USER_ACTION_VALIDATOR_DELEGATE           = 'd'
USER_ACTION_VALIDATOR_LIST_UNDELEGATIONS = 'l'
USER_ACTION_VALIDATOR_UNDELEGATE         = 'u'
USER_ACTION_VALIDATOR_SWITCH             = 's'

# Max number of validators that Luna Classic allows
MAX_VALIDATOR_COUNT = 100

# Governance constants:
PROPOSAL_STATUS_UNSPECIFIED    = 0
PROPOSAL_STATUS_DEPOSIT_PERIOD = 1
PROPOSAL_STATUS_VOTING_PERIOD  = 2
PROPOSAL_STATUS_PASSED         = 3
PROPOSAL_STATUS_REJECTED       = 4
PROPOSAL_STATUS_FAILED         = 5

PROPOSAL_VOTE_EMPTY        = 0
PROPOSAL_VOTE_YES          = 1
PROPOSAL_VOTE_ABSTAIN      = 2
PROPOSAL_VOTE_NO           = 3
PROPOSAL_VOTE_NO_WITH_VETO = 4

# Coin constants:
AACRE     = 'aacre'
AARCH     = 'aarch'
ACANTO    = 'acanto'
ACUDOS    = 'acudos'
AEVMOS    = 'aevmos'
AFET      = 'afet'
ANOM      = 'anom'
APLANQ    = 'aplanq'
AREBUS    = 'arebus'
BASECRO   = 'basecro'
INJ       = 'inj'
LOKI      = 'loki'
NANOLIKE  = 'nanolike'
NCHEQ     = 'ncheq'
ORAI      = 'orai'
ROWAN     = 'rowan'
SWTH      = 'swth'
UAKT      = 'uakt'
UATOM     = 'uatom'
UAXL      = 'uaxl'
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
UIOV      = 'uiov'
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
UTICK     = 'utick'
UUMEE     = 'uumee'
UUSD      = 'uusd'
UUSDC     = 'uusdc'
UVDL      = 'uvdl'
UWHALE    = 'uwhale'
UXKI      = 'uxki'
UXPRT     = 'uxprt'
WARB      = 'arb-wei'
WAVAX     = 'wavax-wei'
WBNB      = 'wbnb-wei'
WBTC      = 'wbtc-satoshi'
WDAI      = 'dai-wei'
WDOT      = 'dot-planck'
WETH      = 'weth-wei'
WFRAX     = 'frax-wei'
WFTM      = 'wftm-wei'
WLINK     = 'link-wei'
WMATIC    = 'wmatic-wei'

# Coin keys and display values:
# NOTE: This is in display order, not sorted by key
FULL_COIN_LOOKUP = {
    UAKT:      'Akash',
    AACRE:     'Arable Protocol',
    AARCH:     'Archway',
    UMNTL:     'AssetMantle',
    UATOM:     'Atom',
    'uaud':    'AUTC',
    UAXL:      'Axelar',
    UBAND:     'Band Protocol',
    UBASE:     'BASE',
    UBTSG:     'Bitsong',
    UBNT:      'Bluzelle',
    ACANTO:    'Canto',
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
    UTICK:     'Microtick',
    'umnt':    'MNTC',
    'umyr':    'MYTC',
    'unok':    'NOTC',
    LOKI:      'Odin protocol',
    ANOM:      'Onomy Protocol',
    ORAI:      'Oraichain',
    UOSMO:     'OSMO',
    UXPRT:     'Persistance',
    'uphp':    'PHTC',
    APLANQ:    'Planq',
    AREBUS:    'Rebus',
    UREGEN:    'Regen',
    USCRT:     'Secret',
    'usdr':    'SDTC',
    UDVPN:     'Sentinel',
    'usek':    'SETC',
    'usgd':    'SGTC',
    UCTK:      'Shentu',
    ROWAN:     'Sifchain',
    USOMM:     'Sommelier',
    USTARS:    'Stargaze',
    UIOV:      'Starname',
    USTRD:     'Stride',
    'uthb':    'THTC',
    'utwd':    'TWTC',
    UUMEE:     'Umee',
    UUSD:      'USTC',
    UUSDC:     'USDC',
    UVDL:      'Vidulum',
    UWHALE:    'Whale',
    WARB:      'wARB',
    WAVAX:     'wAVAX',
    WBNB:      'wBNB',
    WBTC:      'wBTC',
    WDAI:      'wDAI',
    WDOT:      'wDOT',
    WETH:      'wETH',
    WFRAX:     'wFRAX',
    WFTM:      'wFTM',
    WLINK:     'wLINK',
    WMATIC:    'wMATIC'
}

BASIC_COIN_LOOKUP = {
    ULUNA: 'LUNC',
    UUSD:  'USTC'
}

# These coins will be removed from the full coin lookup
# They used to work, but were disabled by a change on the columbus-5 chain
DISABLED_COINS = [
    'uaud',
    'ucad',
    'uchf',
    'ucny',
    'udkk',
    'ueur',
    'ugbp',
    'uhkd',
    'uidr',
    'uinr',
    'ujpy',
    'umnt',
    'umyr',
    'unok',
    'uphp',
    'usdr',
    'usek',
    'usgd',
    'uthb',
    'utwd'
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
    ULUNA: {
        'chain_id':      'columbus-5',
        'coingecko_id':  'terra-luna',
        'cosmos_name':   'terra',
        'ibc_channels':  {
            'uosmo': 'channel-1',
        },
        'lcd_urls':      ['https://terra-classic-fcd.publicnode.com', 'https://rest.cosmos.directory/terra', 'https://terra-classic-fcd.publicnode.com'],
        'precision':     6,
        'bech32_prefix': 'terra'
    },
    UOSMO: {
        'chain_id':      'osmosis-1',
        'coingecko_id':  'osmosis',
        'cosmos_name':   'osmosis',
        'ibc_channels':  {
            AACRE:     'channel-490',
            AARCH:     'channel-1429',
            ACANTO:    'channel-550',
            ACUDOS:    'channel-298',
            AEVMOS:    'channel-204',
            AFET:      'channel-229',
            ANOM:      'channel-525',
            APLANQ:    'channel-492',
            AREBUS:    'channel-355',
            BASECRO:   'channel-5',
            INJ:       'channel-122',
            LOKI:      'channel-258',
            NANOLIKE:  'channel-53',
            NCHEQ:     'channel-108',
            ORAI:      'channel-216',
            ROWAN:     'channel-47',
            SWTH:      'channel-188',
            UAKT:      'channel-1',
            UAXL:      'channel-208',
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
            UIOV:      'channel-15',
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
            UTICK:     'channel-39',
            UUMEE:     'channel-184',
            UUSD:      'channel-72',
            UUSDC:     'channel-208',
            UVDL:      'channel-124',
            UWHALE:    'channel-84',
            UXKI:      'channel-77',
            UXPRT:     'channel-4',
            WARB:      'channel-208',
            WAVAX:     'channel-208',
            WBNB:      'channel-208',
            WBTC:      'channel-208',
            WDAI:      'channel-208',
            WDOT:      'channel-208',
            WETH:      'channel-208',
            WFRAX:     'channel-208',
            WFTM:      'channel-208',
            WLINK:     'channel-208',
            WMATIC:    'channel-208'
        },
        'lcd_urls':      ['https://lcd.osmosis.zone'],
        'precision':     6,
        'bech32_prefix': 'osmo'
    },
    AACRE: {
        'coingecko_id':  'arable-protocol',
        'cosmos_name':   'acrechain',
        'precision':     18,
        'bech32_prefix': 'acre'
    },
    AARCH: {
        'coingecko_id':  'archway',
        'cosmos_name':   'archway',
        'precision':     18,
        'bech32_prefix': 'archway'
    },
    ACANTO: {
        'coingecko_id':  'canto',
        'cosmos_name':   'canto',
        'precision':     18,
        'bech32_prefix': 'canto'
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
    ANOM: {
        'coingecko_id':  'onomy-protocol',
        'cosmos_name':   'onomy',
        'precision':     18,
        'bech32_prefix': 'onomy'
    },
    APLANQ: {
        'coingecko_id':  'planq',
        'cosmos_name':   'planq',
        'precision':     18,
        'bech32_prefix': 'plq'
    },
    AREBUS: {
        'coingecko_id':  'rebus',
        'cosmos_name':   'rebus',
        'precision':     18,
        'bech32_prefix': 'rebus'
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
    ROWAN: {
        'coingecko_id':  'sifchain',
        'cosmos_name':   'sifchain',
        'precision':     18,
        'bech32_prefix': 'sif'
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
    UAXL: {
        'coingecko_id':  'axelar',
        'cosmos_name':   'axelar',
        'precision':     6,
        'bech32_prefix': 'axelar'
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
    UIOV: {
        'coingecko_id':  'starname',
        'cosmos_name':   'starname',
        'precision':     6,
        'bech32_prefix': 'star'
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
    UTICK: {
        'coingecko_id':  'microtick',
        'cosmos_name':   'microtick',
        'precision':     6,
        'bech32_prefix': 'micro'
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
    UUSDC: {
        'coingecko_id':  'usd-coin',
        'cosmos_name':   'axelar',
        'precision':     6,
        'bech32_prefix': 'axelar'
    },
    UVDL: {
        'coingecko_id':  'vidulum',
        'cosmos_name':   'vidulum',
        'precision':     6,
        'bech32_prefix': 'vdl'
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
    WARB: {
        'coingecko_id':  'arbitrum',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    },
    WAVAX: {
        'coingecko_id':  'avalanche-2',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    },
    WBNB: {
        'coingecko_id':  'binancecoin',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    },
    WBTC: {
        'coingecko_id':  'bitcoin',
        'cosmos_name':   'axelar',
        'precision':     8,
        'bech32_prefix': 'axelar'
    },
    WDAI: {
        'coingecko_id':  'dai',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    },
    WDOT: {
        'coingecko_id':  'polkadot',
        'cosmos_name':   'axelar',
        'precision':     10,
        'bech32_prefix': 'axelar'
    },
    WETH: {
        'coingecko_id':  'ethereum',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    },
    WFRAX: {
        'coingecko_id':  'frax',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    },
    WFTM: {
        'coingecko_id':  'fantom',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    },
    WLINK: {
        'coingecko_id':  'chainlink',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    },
    WMATIC: {
        'coingecko_id':  'matic-network',
        'cosmos_name':   'axelar',
        'precision':     18,
        'bech32_prefix': 'axelar'
    }
}

OFFCHAIN_COINS = []
for item in CHAIN_DATA[UOSMO]['ibc_channels'].keys():
    if item != ULUNA:
        OFFCHAIN_COINS.append(item)

# Remove any disabled coins
if HIDE_DISABLED_COINS == True:
    for item in DISABLED_COINS:
        if item in FULL_COIN_LOOKUP:
            del(FULL_COIN_LOOKUP[item])