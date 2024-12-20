#!/usr/bin/python3

# ************************************************************
# Copyright © 2003-2024 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import names
import argparse
import logging
from os.path import exists, dirname, realpath, join
from uuid import uuid4
from getpass import getpass

from constants import ROOT_USER_ID, ROOT_ORGANIZATION_ID
from utils import hash, sqlite_connect
from datatypes import OrganizationKind

logging.basicConfig(format='[create_db.py] %(asctime)s -- %(message)s', encoding='utf-8', level=logging.INFO)

def main(args):
    filename = join(dirname(realpath(__file__)), f'{args.db_name}.db')

    if exists(filename):
        logging.error(f'{filename} already exists. Either specify a new file name or move/delete the file.')
        return

    logging.info(f'Creating DB file {filename}...')
    root_user = input('Enter root username: ').strip()
    root_pwd = hash(getpass(f'Enter password for root user: ').strip())

    db = sqlite_connect(filename)
    db.execute('CREATE TABLE IF NOT EXISTS users (id VARCHAR(36) NOT NULL PRIMARY KEY, login NVARCHAR(255) UNIQUE, name NVARCHAR(255), email VARCHAR(255), password VARCHAR(255), organization_id VARCHAR(36) REFERENCES organizations(id) ON DELETE CASCADE) WITHOUT ROWID')

    db.execute('CREATE TABLE IF NOT EXISTS organizations (id VARCHAR(36) NOT NULL PRIMARY KEY, parent_id VARCHAR(36) REFERENCES organizations(id) ON DELETE CASCADE, name VARCHAR(255), kind TINYINT) WITHOUT ROWID')
    db.execute('CREATE TABLE IF NOT EXISTS organizations_mapping (organization_id VARCHAR(36) PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE, acronis_tenant_id VARCHAR(36) UNIQUE, acronis_dc_url VARCHAR(64)) WITHOUT ROWID')

    db.execute('CREATE INDEX IF NOT EXISTS organization_parent_idx ON organizations(parent_id)')

    db.execute('INSERT INTO organizations VALUES (?,?,?,?)', (ROOT_ORGANIZATION_ID, None, 'John Doe Inc.', OrganizationKind.PARTNER))
    for _ in range(5):
        child_id = str(uuid4())
        user_id = str(uuid4())
        name = names.get_full_name()
        login = name.lower().replace(' ', '.')
        db.execute('INSERT INTO organizations VALUES (?,?,?,?)', (child_id, ROOT_ORGANIZATION_ID, f'{name} Inc.', OrganizationKind.CUSTOMER))
        db.execute('INSERT INTO users VALUES (?,?,?,?,?,?)', (user_id, login, name, f'{login}@john-doe.xyz', None, child_id))

    db.execute('INSERT INTO users VALUES (?,?,?,?,?,?)', (ROOT_USER_ID, root_user, 'John Doe', f'{root_user}@john-doe.xyz', root_pwd, ROOT_ORGANIZATION_ID))
    for _ in range(5):
        name = names.get_full_name()
        login = name.lower().replace(' ', '.')
        db.execute('INSERT INTO users VALUES (?,?,?,?,?,?)', (str(uuid4()), login, name, f'{login}@john-doe.xyz', None, ROOT_ORGANIZATION_ID))

    db.commit()
    db.close()
    logging.info(f'Done.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-name',  help='Database name', default='vendor')
    args = parser.parse_args()

    main(args)
