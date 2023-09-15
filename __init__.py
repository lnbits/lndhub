from fastapi import APIRouter

from lnbits.db import Database
from lnbits.helpers import template_renderer

db = Database("ext_lndhub")

lndhub_ext: APIRouter = APIRouter(prefix="/lndhub", tags=["lndhub"])

lndhub_static_files = [
    {
        "path": "/lndhub/static",
        "name": "lndhub_static",
    }
]


def lndhub_renderer():
    return template_renderer(["lndhub/templates"])


from .decorators import *  # noqa: F401,F403
from .utils import *  # noqa: F401,F403
from .views import *  # noqa: F401,F403
from .views_api import *  # noqa: F401,F403
