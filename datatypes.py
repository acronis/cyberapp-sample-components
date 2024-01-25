# ************************************************************
# Copyright © 2003-2023 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

from typing import TypedDict, Any
from enum import IntEnum

class OrganizationKind(IntEnum):
    PARTNER = 0
    CUSTOMER = 1

OrganizationKindMapping: dict[str, OrganizationKind] = {
    OrganizationKind.PARTNER.name: OrganizationKind.PARTNER,
    OrganizationKind.CUSTOMER.name: OrganizationKind.CUSTOMER
}

class CallbackContext(TypedDict):
    callback_id: str
    endpoint_id: str
    tenant_id: str
    datacenter_url: str

class CallbackResponse(TypedDict):
    type: str
    request_id: str
    response_id: str
    payload: dict[str, Any]

class CallbackRequest(TypedDict):
    type: str
    request_id: str
    created_at: str
    context: CallbackContext
    payload: dict[str, Any]

class TopologyInfo(TypedDict):
    id: str
    name: str

class OrganizationMappingPair(TypedDict):
    acronis_tenant_id: str
    vendor_tenant_id: str
    acronis_dc_url: str

class UserData(TypedDict):
    id: str
    name: str
    email: str

class OrganizationData(TypedDict):
    id: str
    parent_id: str
    name: str
    kind: OrganizationKind
