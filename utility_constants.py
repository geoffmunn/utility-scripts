#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# User settings - can be changed if required
TESTMODE = False
WITHDRAWAL_REMAINDER = 250   # This is the amount of Lunc we want to keep after withdrawal and before delegating. You should never delegate the entire balance.
SEARCH_RETRY_COUNT   = 30    # This is the number of times we will check for a transaction to appear in the chain before deciding it didn't work.

# System settings - these can be changed, but shouldn't be necessary
#LCD_ENDPOINT             = 'https://lcd.terrarebels.net'
#LCD_ENDPOINT             = 'https://lcd.terra.dev'
LCD_ENDPOINT             = 'https://terra-classic-lcd.publicnode.com'
GAS_PRICE_URI            = 'https://terra-classic-fcd.publicnode.com/v1/txs/gas_prices'
TAX_RATE_URI             = 'https://terra-classic-lcd.publicnode.com/terra/treasury/v1beta1/tax_rate'
TOKEN_LIST               = 'https://assets.terrarebels.net/cw20/tokens.json'
CONFIG_FILE_NAME         = 'user_config.yml'
GAS_ADJUSTMENT           = 1
GAS_ADJUSTMENT_SEND      = 3.5
GAS_ADJUSTMENT_SWAPS     = 3.5
GAS_ADJUSTMENT_INCREMENT = 0.1
MAX_GAS_ADJUSTMENT       = 4

# Swap contracts can be found here
# https://assets.terra.money/cw20/pairs.dex.json
#TERRASWAP_UUSD_TO_ULUNA_ADDRESS = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
ASTROPORT_UUSD_TO_ULUNA_ADDRESS = 'terra1m6ywlgn6wrjuagcmmezzz2a029gtldhey5k552'
#TERRASWAP_UKRW_TO_ULUNA_ADDRESS = 'terra1erfdlgdtt9e05z0j92wkndwav4t75xzyapntkv'
TERRASWAP_ULUNA_TO_UUSD_ADDRESS = 'terra1l7vy20x940je7lskm6x9s839vjsmekz9k9mv7g'
#ASTROPORT_UUSD_TO_MINA_ADDRESS  = 'terra134m8n2epp0n40qr08qsvvrzycn2zq4zcpmue48'
#TERRASWAP_UKRT_TO_LUNC_ADDRESS  = 'terra1erfdlgdtt9e05z0j92wkndwav4t75xzyapntkv'

# GRT TO UUSD transaction example:
#https://finder.terrarebels.net/classic/tx/6316DD186EFB35BBC7940B5B9D252977721D7C99D23DCF554A8AF70A8C3FB57A

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