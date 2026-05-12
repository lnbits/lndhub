import os
from typing import Any, cast

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from lnbits.core import migrations as core_migrations
from lnbits.core.db import db as core_db
from lnbits.core.helpers import run_migration

from .. import lndhub_ext


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_ext():
    if os.path.isfile(core_db.path):
        os.remove(core_db.path)
    async with core_db.connect() as conn:
        await run_migration(conn, core_migrations, "core")


@pytest_asyncio.fixture
async def client():
    app = FastAPI()
    app.include_router(lndhub_ext)
    transport = ASGITransport(app=cast(Any, app))

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
