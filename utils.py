# ************************************************************
# Copyright © 2003-2023 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import sqlite3
from argon2 import PasswordHasher

h = PasswordHasher()


def hash(text: str) -> str:
    return h.hash(text)


def verify(hash: str, password: str) -> bool:
    return h.verify(hash, password)


def sqlite_connect(filename: str) -> sqlite3.Connection:
    db = sqlite3.connect(filename)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=normal')
    db.execute('PRAGMA journal_size_limit=67110000')
    return db
