from fastapi import Depends, Request, APIRouter

from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

def lndhub_renderer():
    return template_renderer(["lndhub/templates"])

lndhub_generic_router = APIRouter()

@lndhub_generic_router.get("/")
async def lndhub_index(request: Request, user: User = Depends(check_user_exists)):
    return lndhub_renderer().TemplateResponse(
        "lndhub/index.html", {"request": request, "user": user.dict()}
    )
