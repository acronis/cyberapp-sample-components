#!/usr/bin/python3

# ************************************************************
# Copyright © 2003-2023 Acronis International GmbH.
# This source code is distributed under MIT software license.
# ************************************************************

import ssl
import logging
import argparse
from os.path import join, dirname, realpath
from aiohttp import web

import server.routes as routes
from utils import sqlite_connect

logging.basicConfig(format='[Service] %(asctime)s -- %(message)s', encoding='utf-8', level=logging.INFO)


@web.middleware
async def req_logger(request: web.Request, handler):
    logging.info(f'Headers {request.headers}')
    return await handler(request)


def main(args):
    filename = join(dirname(realpath(__file__)), f'{args.db_name}.db')

    db = sqlite_connect(filename)

    app = web.Application(middlewares=[req_logger])
    app['db'] = db
    routes.setup(app)

    if args.certfile and args.keyfile:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(args.certfile, args.keyfile)
        web.run_app(app, port=443 if not args.port else args.port, ssl_context=ssl_ctx)
    else:
        web.run_app(app, port=8080 if not args.port else args.port)

    db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--certfile', help='Path to certificate\'s file.')
    parser.add_argument('--keyfile',  help='Path to certificate\'s private key.')
    parser.add_argument('--db-name',  help='Database name', default='vendor')
    parser.add_argument('--port',  help='Web server\'s port')

    args = parser.parse_args()

    main(args)
