# ************************************************************
# Copyright © 2003-2024 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import sqlite3
from typing import Optional
from uuid import uuid4
from datatypes import *
from aiohttp import web
from constants import APPCODE

def callback_user_write(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: dict) -> web.Response:
    data = conn.execute('SELECT organization_id FROM organizations_mapping WHERE acronis_tenant_id = ?', (context['tenant_id'],)).fetchone()
    if not data:
        return web.json_response(
            status=200,
            data=CallbackResponse(
                type=f'cti.a.p.acgw.response.v1.0~{APPCODE}.user_write_success.v1.0',
                request_id=request_id,
                response_id=response_id
            )
        )

    conn.execute('INSERT INTO users VALUES (?,?,?,?,?,?)', (str(uuid4()), payload['login'], payload['name'], payload['email'], None, data['organization_id']))
    conn.commit()
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type=f'cti.a.p.acgw.response.v1.0~{APPCODE}.user_write_success.v1.0',
            request_id=request_id,
            response_id=response_id
        )
    )

def callback_user_update(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: dict) -> web.Response:
    data = conn.execute('SELECT organization_id FROM organizations_mapping WHERE acronis_tenant_id = ?', (context['tenant_id'],)).fetchone()
    if not data:
        return web.json_response(
            status=200,
            data=CallbackResponse(
                type=f'cti.a.p.acgw.response.v1.0~{APPCODE}.user_update_success.v1.0',
                request_id=request_id,
                response_id=response_id
            )
        )

    conn.execute(f'UPDATE users SET name = ?, email = ? WHERE id = ? AND organization_id = ?', (payload['name'], payload['email'], payload['id'], data['organization_id']))
    conn.commit()
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type=f'cti.a.p.acgw.response.v1.0~{APPCODE}.user_update_success.v1.0',
            request_id=request_id,
            response_id=response_id
        )
    )

def callback_user_delete(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: dict) -> web.Response:
    data = conn.execute('SELECT organization_id FROM organizations_mapping WHERE acronis_tenant_id = ?', (context['tenant_id'],)).fetchone()
    if not data:
        return web.json_response(
            status=200,
            data=CallbackResponse(
                type=f'cti.a.p.acgw.response.v1.0~{APPCODE}.user_delete_success.v1.0',
                request_id=request_id,
                response_id=response_id
            )
        )

    conn.execute('DELETE FROM users WHERE id = ? AND organization_id = ?', (payload['id'], data['organization_id']))
    conn.commit()
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type=f'cti.a.p.acgw.response.v1.0~{APPCODE}.user_delete_success.v1.0',
            request_id=request_id,
            response_id=response_id
        )
    )

def callback_users_read(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: Optional[dict]) -> web.Response:
    data = conn.execute('SELECT organization_id FROM organizations_mapping WHERE acronis_tenant_id = ?', (context['tenant_id'],)).fetchone()
    if not data:
        return web.json_response(
            status=200,
            data=CallbackResponse(
                type=f'cti.a.p.acgw.response.v1.0~{APPCODE}.users_read_success.v1.0',
                request_id=request_id,
                response_id=response_id,
                payload={ 'items': [] }
            )
        )

    data: list[UserData] = [
        dict(row)
        for row in conn.execute(
            '''WITH RECURSIVE organizations_tree AS (
                SELECT id, name, kind, parent_id AS direct_parent_id, parent_id FROM organizations

                UNION ALL

                SELECT p.id, p.name, p.kind, p.parent_id AS direct_parent_id, (SELECT parent_id FROM organizations WHERE id = p.parent_id) AS parent
                FROM organizations_tree AS p
                WHERE parent IS NOT NULL
            )

            SELECT id, name, email FROM users 
            WHERE organization_id IN (
                SELECT orgs.id FROM organizations_tree AS orgs 
                JOIN organizations_mapping AS map 
                ON orgs.id = map.organization_id WHERE orgs.parent_id = ?
            ) OR organization_id = ?''', (data['organization_id'], data['organization_id'])
        ).fetchall()
    ]
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type=f'cti.a.p.acgw.response.v1.0~{APPCODE}.users_read_success.v1.0',
            request_id=request_id,
            response_id=response_id,
            payload={ 'items': data }
        )
    )


# custom callbacks
mapping = {
    f'cti.a.p.acgw.callback.v1.0~{APPCODE}.users_read.v1.0': callback_users_read,
    f'cti.a.p.acgw.callback.v1.0~{APPCODE}.user_write.v1.0': callback_user_write,
    f'cti.a.p.acgw.callback.v1.0~{APPCODE}.user_update.v1.0': callback_user_update,
    f'cti.a.p.acgw.callback.v1.0~{APPCODE}.user_delete.v1.0': callback_user_delete,
}
