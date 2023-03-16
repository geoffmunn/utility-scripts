#!/usr/bin/env python3

# User settings - can be changed if required
WITHDRAWAL_REMAINDER = 250   # This is the amount of Lunc we want to keep after withdrawal and before delegating. You should never delegate the entire balance.
SEARCH_RETRY_COUNT   = 30

# System settings - these can be changed, but shouldn't be necessary
GAS_PRICE_URI       = 'https://fcd.terra.dev/v1/txs/gas_prices'
TAX_RATE_URI        = 'https://lcd.terra.dev/terra/treasury/v1beta1/tax_rate'
CONFIG_FILE_NAME    = 'user_config.yml'
GAS_ADJUSTMENT      = 3

# Swap contracts can be found here
# https://assets.terra.money/cw20/pairs.dex.json
UUSD_TO_ULUNA_SWAP_ADDRESS      = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
ASTROPORT_UUSD_TO_ULUNA_ADDRESS = 'terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552'
ASTROPORT_UUSD_TO_MINA_ADDRESS = 'terra134m8n2epp0n40qr08qsvvrzycn2zq4zcpmue48'

# Do not change these
USER_ACTION_ALL               = 'a'
USER_ACTION_DELEGATE          = 'd'
USER_ACTION_SWAP              = 's'
USER_ACTION_SWAP_DELEGATE     = 'sd'
USER_ACTION_WITHDRAW          = 'w'
USER_ACTION_WITHDRAW_DELEGATE = 'wd'

COIN_DIVISOR = 1000000
MAX_VALIDATOR_COUNT = 130

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