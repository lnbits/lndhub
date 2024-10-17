from base64 import b64decode

from fastapi import Request, Security
from fastapi.security.api_key import APIKeyHeader
from lnbits.core.models import WalletTypeInfo
from lnbits.decorators import require_admin_key, require_invoice_key

api_key_header_auth = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description="Admin or Invoice key for LNDHub API's",
)


async def sanitize_token(api_key: str) -> str:
    if api_key.startswith("Bearer "):
        t = api_key.split(" ")[1]
        _, token = b64decode(t).decode().split(":")
    else:
        token = api_key
    return token


async def lndhub_require_admin_key(
    request: Request, api_key_header_auth: str = Security(api_key_header_auth)
):
    token = await sanitize_token(api_key_header_auth)
    return await require_admin_key(request, token)


async def lndhub_require_invoice_key(
    request: Request, api_key_header_auth: str = Security(api_key_header_auth)
) -> WalletTypeInfo:
    token = await sanitize_token(api_key_header_auth)
    return await require_invoice_key(request, token)
