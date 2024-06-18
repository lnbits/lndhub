from fastapi import APIRouter

from lnbits.db import Database
from .views_api import lndhub_api_router
from .views import lndhub_generic_router

db = Database("ext_lndhub")
lndhub_ext: APIRouter = APIRouter(prefix="/lndhub", tags=["lndhub"])
lndhub_static_files = [
    {
        "path": "/lndhub/static",
        "name": "lndhub_static",
    }
]

lndhub_ext.include_router(lndhub_generic_router)
lndhub_ext.include_router(lndhub_api_router)
