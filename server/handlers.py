# ************************************************************
# Copyright © 2003-2024 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import json
import logging
import traceback
import sqlite3
from uuid import uuid4
from base64 import b64decode
from aiohttp import web
from typing import Optional

from datatypes import *
from utils import verify
from server.callbacks import CALLBACKS_MAPPING


def _get_authenticated_user(db: sqlite3.Connection, identity: str, password: str) -> Optional[dict]:
    row = db.execute('SELECT id, organization_id, password FROM users WHERE login = ? AND password IS NOT NULL', (identity.lower(),)).fetchone()
    verify(row['password'], password)
    return { 'id': row['id'], 'organization_id': row['organization_id'] }


async def index(_: web.Request) -> web.Response:
    return web.Response(text='Hello there! Send POST requests to the /callback endpoint.', content_type='text/plain')


async def callback_handler(request: web.Request) -> web.Response:
    if not request.content_type.startswith('application/json'):
        logging.info(f'Received non-JSON request')
        return web.Response(status=400)

    response_id = str(uuid4())
    data: CallbackRequest = await request.json()
    logging.info(f'Received data {data}')
    try:
        callback_id = data['context']['callback_id']
        if callback_id not in CALLBACKS_MAPPING:
            logging.info(f'Callback not found.')
            return web.json_response(status=400, data={'response_id': response_id, 'message': 'Callback not found.'})
    except:
        logging.info(f'Received malformed callback request.')
        logging.info(traceback.format_exc())
        return web.json_response(status=400, data={'response_id': response_id, 'message': 'Received malformed callback request.'})

    try:
        raw_creds = b64decode(request.headers['X-CyberApp-Auth']).decode()
        sep_idx = raw_creds.index(':')
        identity, secrets = [raw_creds[:sep_idx], json.loads(raw_creds[sep_idx + 1:])]
        # extra = json.loads(b64decode(request.headers['X-CyberApp-Extra']).decode())

        with request.app['db'] as conn:
            row = _get_authenticated_user(conn, identity, secrets['password'])
    except Exception as e:
        logging.info(f'Failed to authenticate user. Reason: {e}')
        logging.info(traceback.format_exc())
        return web.json_response(status=401, data={'response_id': response_id, 'message': f'Failed to authenticate user.'})
    
    payload = data.get('payload', {})
    with request.app['db'] as conn:
        try:
            res = CALLBACKS_MAPPING[callback_id](conn, row['organization_id'], data['request_id'], response_id, data['context'], payload)
            logging.info(f'Response data: {res.body}')
        except Exception as e:
            res = web.json_response(status=500, data={'response_id': response_id, 'message': f'Failed to make proper response. Reason: {e}'})
            logging.info(f'Failed to make proper response. Reason: {e}')
            logging.info(traceback.format_exc())
    return res
