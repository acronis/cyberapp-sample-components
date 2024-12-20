# ************************************************************
# Copyright © 2003-2024 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import server.callbacks.enablement as enablement
import server.callbacks.user_management as user_management

CALLBACKS_MAPPING = {
    **enablement.mapping,
    **user_management.mapping,
}
