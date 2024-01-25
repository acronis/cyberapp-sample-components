# ************************************************************
# Copyright © 2003-2023 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

from random import choice
from constants import APPCODE

ALERT_TEMPLATES = [
    # {
    #     "type": f"cti.a.p.am.alert.v1.0~a.p.basic.v1.0~{APPCODE}.malware_detected.v1.0",
    #     "category": f"cti.a.p.am.category.v1.0~{APPCODE}.protection.v1.0",
    #     "details": {
    #         "title": "Malware Quarantined",
    #         "category": "Malware Detected",
    #         "description": "Malicious file \"trojan.exe\" was put into quarantine.",
    #         "fields": {
    #             "Malware type": "Trojan:Win32/Caphaw.D!lnk",
    #             "Device ID": "62aedd2b-6556-45d5-a76e-43db475068a7",
    #             "Full path": "C:\\Windows\\System32\\trojan.exe"
    #         }
    #     }
    # },
    # 1. Copy the template above and place it below.
    # 2. Replace "type" with CTI of your alert type.
    # 3. Replace "category" with CTI of your alert category.
    # 4. Replace the values in the "details" field as necessary.
]

WORKLOAD_TEMPLATES = [
    # {
    #     "type": f"cti.a.p.wm.workload.v1.0~a.p.wm.aspect.v1.0~{APPCODE}.virtual_machine.v1.0",
    #     "name": "Customer's Workload",
    #     # Add attributes as defined in the Vendor Portal
    #     "attributes": {},
    #     "enabled": True,
    # },
    # 1. Copy the template above and place it below.
    # 2. Replace "type" with CTI of your alert type.
    # 3. Replace the values in the "attributes" field as necessary.
]

def get_random_alert(tenant_id: str) -> dict:
    if not ALERT_TEMPLATES:
        raise Exception('Specify alert templates in generator.py')
    return { **choice(ALERT_TEMPLATES), "tenantID": tenant_id }

def get_random_workload(tenant_id: str) -> dict:
    if not WORKLOAD_TEMPLATES:
        raise Exception('Specify workload templates in generator.py')
    return { "items": [{**choice(WORKLOAD_TEMPLATES), "tenant_id": tenant_id}] }
