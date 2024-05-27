from base64 import b64decode

from fastapi import Request, status
from fastapi.param_functions import Security
from fastapi.security.api_key import APIKeyHeader
from starlette.exceptions import HTTPException

from lnbits.decorators import get_key_type
from lnbits.core.models import WalletTypeInfo

api_key_header_auth = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description="Admin or Invoice key for LNDHub API's",
)


async def check_wallet(
    r: Request, api_key: str = Security(api_key_header_auth)
) -> WalletTypeInfo:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth key"
        )
    if api_key.startswith("Bearer "):
        t = api_key.split(" ")[1]
        _, token = b64decode(t).decode().split(":")
    else:
        token = api_key

    return await get_key_type(r, api_key_header=token)


async def require_admin_key(
    r: Request, api_key_header_auth: str = Security(api_key_header_auth)
):
    wallet = await check_wallet(r, api_key_header_auth)
    if wallet.key_type != 0:
        # If wallet type is not admin then return the unauthorized status
        # This also covers when the user passes an invalid key type
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin key required."
        )
    else:
        return wallet
