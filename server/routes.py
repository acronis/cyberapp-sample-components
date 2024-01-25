# ************************************************************
# Copyright © 2003-2023 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

from aiohttp import web

import server.handlers as handlers

ROUTES = (
    web.RouteDef('GET',  '/',         handler=handlers.index,            kwargs={'name': 'index'}),
    web.RouteDef('POST', '/callback', handler=handlers.callback_handler, kwargs={'name': 'callback'})
)

def setup(app: web.Application):
    app.router.add_routes(ROUTES)
