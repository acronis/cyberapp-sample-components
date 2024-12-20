# ************************************************************
# Copyright © 2003-2024 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import aiohttp
from base64 import b64encode
from typing import Optional, TypedDict


class OAuth2TokenInfo(TypedDict):
    token_type: str
    access_token: str
    id_token: str
    expires_in: int
    refresh_token: Optional[str]


class ApiClient:

    def __init__(self, dc_url: str, client_id: str, client_secret: str) -> None:
        self.dc_url = dc_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.session: aiohttp.ClientSession = None


    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={ 'User-Agent': 'ACP 1.0/Vendor Connector' })
        return self


    async def __aexit__(self, *error_details): 
        await self.session.close()


    async def authenticate(self) -> OAuth2TokenInfo:
        encoded_client_creds = b64encode(f'{self.client_id}:{self.client_secret}'.encode('ascii'))
        headers = {'Authorization': f'Basic {encoded_client_creds.decode("ascii")}'}
        res = await self.session.post(f'{self.dc_url}/bc/idp/token', headers=headers, data={'grant_type': 'client_credentials'})
        res.raise_for_status()
        token_info: OAuth2TokenInfo = await res.json()
        self.session.headers['Authorization'] = f'Bearer {token_info["access_token"]}'
        return token_info


    async def post_alerts(self, alert: dict) -> dict:
        res = await self.session.post(
            f'{self.dc_url}/api/alert_manager/v1/alerts',
            json=alert
        )
        res.raise_for_status()
        return await res.json()


    async def post_devices(self, workload: dict) -> None:
        res = await self.session.post(
            f'{self.dc_url}/api/workload_management/v5/workloads',
            json=workload
        )
        res.raise_for_status()
        return
