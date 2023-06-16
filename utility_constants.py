#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# User settings - can be changed if required
TESTMODE = False
WITHDRAWAL_REMAINDER = 250   # This is the amount of Lunc we want to keep after withdrawal and before delegating. You should never delegate the entire balance.
SEARCH_RETRY_COUNT   = 30    # This is the number of times we will check for a transaction to appear in the chain before deciding it didn't work.

# System settings - these can be changed, but shouldn't be necessary
#DEFAULT_CHAIN_ID         = 'columbus-5'
#LCD_ENDPOINT             = 'https://lcd.terrarebels.net'
#LCD_ENDPOINT             = 'https://lcd.terra.dev'
#LCD_ENDPOINT             = 'https://terra-classic-lcd.publicnode.com'
GAS_PRICE_URI            = 'https://terra-classic-fcd.publicnode.com/v1/txs/gas_prices'
TAX_RATE_URI             = 'https://terra-classic-lcd.publicnode.com/terra/treasury/v1beta1/tax_rate'
TOKEN_LIST               = 'https://assets.terrarebels.net/cw20/tokens.json'
CONFIG_FILE_NAME         = 'user_config.yml'
GAS_ADJUSTMENT           = 1.1
GAS_ADJUSTMENT_SEND      = 3.6
GAS_ADJUSTMENT_SWAPS     = 3.6
GAS_ADJUSTMENT_INCREMENT = 0.1
MAX_GAS_ADJUSTMENT       = 4

# Swap contracts can be found here
# https://assets.terra.money/cw20/pairs.dex.json
#TERRASWAP_UUSD_TO_ULUNA_ADDRESS = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
#TERRASWAP_UKRW_TO_UUSD_ADDRESS  = 'terra1untf85jwv3kt0puyyc39myxjvplagr3wstgs5s'
#ASTROPORT_UUSD_TO_MINA_ADDRESS  = 'terra134m8n2epp0n40qr08qsvvrzycn2zq4zcpmue48'
ASTROPORT_UUSD_TO_UKUJI_ADDRESS  = 'terra1hasy32pvxmgu485x5tujylemqxynsv72lsu7ve'
ASTROPORT_UUSD_TO_ULUNA_ADDRESS  = 'terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552'
KUJI_SMART_CONTACT_ADDRESS       = 'terra1xfsdgcemqwxp4hhnyk4rle6wr22sseq7j07dnn'
TERRASWAP_UKRW_TO_ULUNA_ADDRESS  = 'terra1erfdlgdtt9e05z0j92wkndwav4t75xzyapntkv'
TERRASWAP_UKUJI_TO_ULUNA_ADDRESS = 'terra19qx5xe6q9ll4w0890ux7lv2p4mf3csd4qvt3ex'
TERRASWAP_ULUNA_TO_UUSD_ADDRESS  = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'

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
MAX_VALIDATOR_COUNT = 130

# Coin constants:

ULUNA = 'uluna'
UKRW  = 'ukrw'
UUSD  = 'uusd'
UKUJI = 'ukuji'

# Coin keys and display values:
FULL_COIN_LOOKUP = {
    'uaud': 'AUT',
    'ucad': 'CAT',
    'uchf': 'CHT',
    'ucny': 'CNT',
    'udkk': 'DKT',
    'ueur': 'EUT',
    'ugbp': 'GBT',
    'uhkd': 'HKT',
    'uidr': 'IDT',
    'uinr': 'INT',
    'ujpy': 'JPT',
    'ukrw': 'KRT',
    #'ukuji': 'KUJI',
    'uluna': 'LUNC',
    'umnt': 'MNT',
    'umyr': 'MYT',
    'unok': 'NOT',
    'uphp': 'PHT',
    'usdr': 'SDT',
    'usek': 'SET',
    'usgd': 'SGT',
    'uthb': 'THT',
    'utwd': 'TWT',
    'uusd': 'UST'
}

BASIC_COIN_LOOKUP = {
    'uluna': 'LUNC',
    'uusd': 'UST'
}

# CHAIN_IDS = {
#     'osmo': 'channel-1',
#     #'cosmos': 'channel-2', # Not active
#     #'emoney': 'channel-5', # Not active
#     #'sif': 'channel-7' # Not active
#     #'inj': 'channel-17' # Not active
#     #'axelar': 'channel-19', # Not active
#     #'juno': 'channel-20' # Not active
#     #'kava': 'channel-24', # Not active
#     #'umee': 'channel-26', # Not active
#     #'omniflix': 'channel-27', # Not active
#     #'evmos': 'channel-51', # Not active
#     #'gravity': 'channel-64' # Not active
#     'kujira': 'channel-71',
#     #'somm': 'channel-83', # Not active
# }
CHAIN_IDS = {
    'terra': {
        'name': 'Luna Classic',
        'chain_id': 'columbus-5',
        'ibc_channels': ['channel-1'],
        'lcd_urls': ['https://rest.cosmos.directory/terra'],
        'denom': 'uluna',
        'status': 'active'
    },
    'osmo': {
        'name': 'Osmosis',
        'chain_id': 'osmosis-1',
        'ibc_channels': ['channel-1'],
        'lcd_urls': ['https://lcd.osmosis.zone'],
        'denom': 'uosmo',
        'status': 'active'
    },
    'kujira': {
        'name': 'Kujira',
        'chain_id': 'kaiyo-1',
        'ibc_channels': 'channel-71',
        'lcd_urls': ['https://rest.cosmos.directory/kujira', 'https://lcd-kujira.mintthemoon.xyz'],
        'denom': 'ukuji',
        'status': 'active'
    }
}
#terra = LCDClient(chain_id="kaiyo-1", url="https://lcd-kujira.mintthemoon.xyz")
#terra = LCDClient(chain_id='kava-9', url="https://api.data.kava.io")
#terra = LCDClient(chain_id='cosmoshub-2', url="https://cosmoshub-lcd.stakely.io")
#terra = LCDClient(chain_id='juno-1', url = 'https://juno-lcd.stakely.io')
#terra=LCDClient(chain_id='emoney-3', url='https://emoney.validator.network/api/')
#terra=LCDClient(chain_id='sifchain-1', url='https://rest.cosmos.directory/sifchain')
#terra=LCDClient(chain_id='injective-1', url='https://rest.cosmos.directory/injective')
#terra=LCDClient(chain_id='axelar-dojo-1', url='https://rest.cosmos.directory/axelar')
#terra=LCDClient(chain_id='umee-1', url='https://rest.cosmos.directory/umee')
#terra=LCDClient(chain_id='omniflixhub-1', url='https://rest.cosmos.directory/omniflixhub')
#terra=LCDClient(chain_id='gravity-bridge-3', url='https://rest.cosmos.directory/gravitybridge')
#terra=LCDClient(chain_id='sommelier-3', url='https://rest.cosmos.directory/sommelier')