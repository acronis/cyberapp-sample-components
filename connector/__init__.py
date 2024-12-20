# ************************************************************
# Copyright © 2003-2024 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import sqlite3
import asyncio
import logging
from random import randint
from datetime import datetime

from datatypes import OrganizationKind
from .generator import get_random_alert, get_random_workload
from .api_client import ApiClient

POST_INTERVAL = 1800 * 1000 # 30 minutes in millis


async def backoff():
    return await asyncio.sleep(randint(50, 250) / 1000) # Between 50 and 250 millis


async def connector(db: sqlite3.Connection, client: ApiClient):
    logging.info('Starting up the connector...')

    logging.info('Authenticating...')
    try:
        await client.authenticate()
    except:
        logging.info('Failed to authenticate')
        return
    logging.info('Successfully authenticated in Acronis!')

    last_post_time = int(datetime.utcnow().timestamp() * 1000) - POST_INTERVAL
    while True:
        now = int(datetime.utcnow().timestamp() * 1000)
        if now - last_post_time < POST_INTERVAL:
            await asyncio.sleep(1)
            continue
        last_post_time = int(datetime.utcnow().timestamp() * 1000)

        logging.info('Got new data! Posting to Acronis...')
        mapping = db.execute('SELECT acronis_tenant_id FROM organizations_mapping AS map LEFT JOIN organizations AS orgs ON orgs.id = map.organization_id WHERE kind = ?', (OrganizationKind.CUSTOMER,)).fetchall()
        for item in mapping:
            logging.info(f'Posting to {item["acronis_tenant_id"]}...')
            alert = get_random_alert(item["acronis_tenant_id"])
            logging.info(f'Alert data: {alert}')
            try:
                data = await client.post_alerts(alert)
                logging.info(f'Done! Response: {data}')
                await backoff()
            except Exception as e:
                logging.info(e)

            workload = get_random_workload(item["acronis_tenant_id"])
            logging.info(f'Workload data: {workload}')
            try:
                await client.post_devices(workload)
                logging.info(f'Done!')
                await backoff()
            except Exception as e:
                logging.info(e)
        logging.info('Finished posting.')
