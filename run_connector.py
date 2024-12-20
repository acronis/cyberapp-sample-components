#!/usr/bin/python3

# ************************************************************
# Copyright © 2003-2024 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import asyncio
import sys
import logging
import argparse
import json
from os.path import join, dirname, realpath

from connector import connector, ApiClient
from utils import sqlite_connect
from dataclasses import dataclass

logging.basicConfig(format='[Connector] %(asctime)s -- %(message)s', encoding='utf-8', level=logging.INFO)

@dataclass
class ConnectorConfig:
    dc_url: str
    client_id: str
    client_secret: str


async def main(args, creds: ConnectorConfig):
    filename = join(dirname(realpath(__file__)), f'{args.db_name}.db')

    db = sqlite_connect(filename)
    async with ApiClient(creds.dc_url, creds.client_id, creds.client_secret) as client:
        await connector(db, client)
    db.close()


if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-path',  help='Path to config file', default='connector.json')
    parser.add_argument('--db-name',  help='Database name', default='vendor')

    args = parser.parse_args()

    with open(args.config_path) as f:
        creds = ConnectorConfig(**json.load(f))

    asyncio.run(main(args, creds))
