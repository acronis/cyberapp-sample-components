# ************************************************************
# Copyright © 2003-2023 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import sqlite3
from typing import Optional
from datatypes import *
from aiohttp import web


def callback_enablement_reset(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: Optional[dict]) -> web.Response:
    conn.execute('DELETE FROM organizations_mapping WHERE organization_id IN (SELECT id FROM organizations WHERE parent_id = ?) OR organization_id = ?', (organization_id, organization_id)).fetchone()
    conn.commit()
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type='cti.a.p.acgw.response.v1.0~a.p.success_no_content.v1.0',
            request_id=request_id,
            response_id=response_id,
        )
    )


def callback_enablement_read(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: Optional[dict]) -> web.Response:
    payload: OrganizationMappingPair = { 'vendor_tenant_id': organization_id }

    row = conn.execute('SELECT acronis_tenant_id FROM organizations_mapping WHERE organization_id = ?', (organization_id,)).fetchone()
    if row:
        payload['acronis_tenant_id'] = row['acronis_tenant_id']

    return web.json_response(
        status=200,
        data=CallbackResponse(
            type='cti.a.p.acgw.response.v1.0~a.p.enablement.read.ok.v1.0',
            request_id=request_id,
            response_id=response_id,
            payload=payload
        )
    )


def callback_enablement_write(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: Optional[dict]) -> web.Response:
    data: Optional[OrganizationMappingPair] = conn.execute('SELECT organization_id FROM organizations_mapping WHERE acronis_tenant_id = ?', (payload['acronis_tenant_id'],)).fetchone()
    # No mapping to this acronis tenant
    if not data:
        data = { 'organization_id': organization_id }
        conn.execute('INSERT OR IGNORE INTO organizations_mapping VALUES (?,?,?)', (organization_id, payload['acronis_tenant_id'], context['datacenter_url']))
        conn.commit()
    # In case there was a mapping to acronis tenant - check if already mapped organization ID matches the credentials
    if data['organization_id'] != organization_id:
        return web.json_response(status=403, data={'response_id': response_id, 'message': 'You\'re not allowed to re-map this organization to different Acronis tenant ID.'})
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type='cti.a.p.acgw.response.v1.0~a.p.success_no_content.v1.0',
            request_id=request_id,
            response_id=response_id
        )
    )


def callback_topology_read(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: Optional[dict]) -> web.Response:
    items: list[TopologyInfo] = [
        { 'id': row['id'], 'name': row['name'] }
        for row in conn.execute(
            '''WITH RECURSIVE organizations_tree AS (
                SELECT id, name, kind, parent_id AS direct_parent_id, parent_id FROM organizations

                UNION ALL

                SELECT p.id, p.name, p.kind, p.parent_id AS direct_parent_id, (SELECT parent_id FROM organizations WHERE id = p.parent_id) AS parent
                FROM organizations_tree AS p
                WHERE parent IS NOT NULL
            )
            SELECT id, name FROM organizations_tree WHERE parent_id = ? AND kind = ?''', 
            (organization_id, OrganizationKind.CUSTOMER)
        ).fetchall()
    ]
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type='cti.a.p.acgw.response.v1.0~a.p.topology.read.ok.v1.0',
            request_id=request_id,
            response_id=response_id,
            payload={ 'items': items }
        )
    )


def callback_tenant_mapping_read(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: Optional[dict]) -> web.Response:
    items: list[OrganizationMappingPair] = [
        dict(row)
        for row in conn.execute(
            '''WITH RECURSIVE organizations_tree AS (
                SELECT id, name, kind, parent_id AS direct_parent_id, parent_id FROM organizations

                UNION ALL

                SELECT p.id, p.name, p.kind, p.parent_id AS direct_parent_id, (SELECT parent_id FROM organizations WHERE id = p.parent_id) AS parent
                FROM organizations_tree AS p
                WHERE parent IS NOT NULL
            )
            SELECT orgs.id AS vendor_tenant_id, map.acronis_tenant_id 
            FROM organizations_tree AS orgs 
            JOIN organizations_mapping AS map ON orgs.id = map.organization_id 
            WHERE (map.acronis_dc_url IS NULL OR map.acronis_dc_url = ?) AND orgs.parent_id = ? AND orgs.kind = ?''',
            (context['datacenter_url'], organization_id, OrganizationKind.CUSTOMER)
        ).fetchall()
    ]
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type='cti.a.p.acgw.response.v1.0~a.p.tenant_mapping.read.ok.v1.0',
            request_id=request_id,
            response_id=response_id,
            payload={ 'items': items }
        )
    )


def callback_tenant_mapping_write(conn: sqlite3.Connection, organization_id: str, request_id: str, response_id: str, context: CallbackContext, payload: Optional[dict]) -> web.Response:
    orgs: list[str] = [
        row['id'] for row in conn.execute(
            '''WITH RECURSIVE organizations_tree AS (
                SELECT id, name, kind, parent_id AS direct_parent_id, parent_id FROM organizations

                UNION ALL

                SELECT p.id, p.name, p.kind, p.parent_id AS direct_parent_id, (SELECT parent_id FROM organizations WHERE id = p.parent_id) AS parent
                FROM organizations_tree AS p
                WHERE parent IS NOT NULL
            )
            SELECT id FROM organizations_tree WHERE parent_id = ? AND kind = ?''',
            (organization_id, OrganizationKind.CUSTOMER)
        ).fetchall()
    ]
    # There's nothing to map if there're no orgs
    if not orgs:
        return web.json_response(status=400, data={'response_id': response_id, 'message': 'Nothing to map'})
    to_insert: list[OrganizationMappingPair] = []

    def conformant_map(modified: list[OrganizationMappingPair]) -> bool:
        for item in modified:
            # Don't allow to overwrite your own mapping and don't allow to write mapping to an org you don't have
            if item['vendor_tenant_id'] not in orgs:
                return False
            if 'acronis_tenant_id' not in item or not item['acronis_tenant_id']:
                conn.execute('DELETE FROM organizations_mapping WHERE organization_id = ?', (item['vendor_tenant_id'],))
                continue
            conn.execute('DELETE FROM organizations_mapping WHERE acronis_tenant_id = ?', (item['acronis_tenant_id'],))
            to_insert.append({'vendor_tenant_id': item['vendor_tenant_id'], 'acronis_tenant_id': item['acronis_tenant_id'], 'acronis_dc_url': context['datacenter_url']})
        conn.executemany('INSERT INTO organizations_mapping VALUES (:vendor_tenant_id, :acronis_tenant_id, :acronis_dc_url) ON CONFLICT(acronis_tenant_id) DO UPDATE SET organization_id = :vendor_tenant_id WHERE acronis_tenant_id = :acronis_tenant_id', to_insert)
        return True

    res = conformant_map(payload['modified'])
    if not res:
        conn.rollback()
        return web.json_response(status=400, data={'response_id': response_id, 'message': 'Failed to write the mapping.'})

    conn.commit()
    return web.json_response(
        status=200,
        data=CallbackResponse(
            type='cti.a.p.acgw.response.v1.0~a.p.success_no_content.v1.0',
            request_id=request_id,
            response_id=response_id
        )
    )


# mandatory callbacks
mapping = {
    'cti.a.p.acgw.callback.v1.0~a.p.enablement.read.v1.0': callback_enablement_read,
    'cti.a.p.acgw.callback.v1.0~a.p.enablement.write.v1.0': callback_enablement_write,
    'cti.a.p.acgw.callback.v1.0~a.p.enablement.reset.v1.0': callback_enablement_reset,
    'cti.a.p.acgw.callback.v1.0~a.p.topology.read.v1.0': callback_topology_read,
    'cti.a.p.acgw.callback.v1.0~a.p.tenant_mapping.read.v1.0': callback_tenant_mapping_read,
    'cti.a.p.acgw.callback.v1.0~a.p.tenant_mapping.write.v1.0': callback_tenant_mapping_write
}
