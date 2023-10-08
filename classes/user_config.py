#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import yaml

from constants.constants import (
    CONFIG_FILE_NAME
)
    
class UserConfig:
    def __init__(self):
        self.user_config = None
        self.file_exists:bool

        try:
            with open(CONFIG_FILE_NAME, 'r') as file:
                self.user_config = yaml.safe_load(file)
                self.file_exists = True
        except:
            self.file_exists = False

    def contents(self) -> str:
        if self.file_exists == True:
            return self.user_config    
        else:
            return ''
