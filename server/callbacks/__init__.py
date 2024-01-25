# ************************************************************
# Copyright © 2003-2023 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import server.callbacks.custom as custom
import server.callbacks.enablement as enablement

CALLBACKS_MAPPING = {
    **enablement.mapping,
    **custom.mapping
}
