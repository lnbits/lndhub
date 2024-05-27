import time
from base64 import urlsafe_b64encode

from fastapi import Depends, Query, APIRouter

from bolt11 import decode as bolt11_decode
from lnbits.core.crud import get_payments
from lnbits.core.services import create_invoice, pay_invoice
from lnbits.core.models import WalletTypeInfo
from lnbits.settings import settings

from .decorators import check_wallet, require_admin_key
from .utils import decoded_as_lndhub, to_buffer
from .models import LndhubAuthData, LndhubCreateInvoice, LndhubAddInvoice

lndhub_api_router = APIRouter(prefix="/ext")

@lndhub_api_router.get("/getinfo")
async def lndhub_getinfo():
    return {"alias": settings.lnbits_site_title}


@lndhub_api_router.post("/auth")
async def lndhub_auth(data: LndhubAuthData):
    token = (
        data.refresh_token
        if data.refresh_token
        else urlsafe_b64encode((data.login + ":" + data.password).encode()).decode(
            "ascii"
        )
    )
    return {"refresh_token": token, "access_token": token}


@lndhub_api_router.post("/addinvoice")
async def lndhub_addinvoice(
    data: LndhubAddInvoice, wallet: WalletTypeInfo = Depends(check_wallet)
):
    try:
        payment_hash, pr = await create_invoice(
            wallet_id=wallet.wallet.id,
            amount=data.amt,
            memo=data.memo or settings.lnbits_site_title,
            extra={"tag": "lndhub"},
        )
    except Exception as exc:
        return {"error": f"Failed to create invoice: {exc!s}"}

    return {
        "pay_req": pr,
        "payment_request": pr,
        "add_index": "500",
        "r_hash": to_buffer(payment_hash),
        "hash": payment_hash,
    }


@lndhub_api_router.post("/payinvoice")
async def lndhub_payinvoice(
    r_invoice: LndhubCreateInvoice,
    key_type: WalletTypeInfo = Depends(require_admin_key),
):
    try:
        invoice = bolt11_decode(r_invoice.invoice)
        await pay_invoice(
            wallet_id=key_type.wallet.id,
            payment_request=r_invoice.invoice,
            extra={"tag": "lndhub"},
        )
    except Exception:
        return {"error": "Payment failed"}

    return {
        "payment_error": "",
        "payment_preimage": "0" * 64,
        "route": {},
        "payment_hash": invoice.payment_hash,
        "decoded": decoded_as_lndhub(invoice),
        "fee_msat": 0,
        "type": "paid_invoice",
        "fee": 0,
        "value": invoice.amount_msat / 1000 if invoice.amount_msat else 0,
        "timestamp": int(time.time()),
        "memo": invoice.description,
    }


@lndhub_api_router.get("/balance")
async def lndhub_balance(
    key_type: WalletTypeInfo = Depends(check_wallet),
):
    return {"BTC": {"AvailableBalance": key_type.wallet.balance}}


@lndhub_api_router.get("/gettxs")
async def lndhub_gettxs(
    key_type: WalletTypeInfo = Depends(check_wallet),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return [
        {
            "payment_preimage": payment.preimage,
            "payment_hash": payment.payment_hash,
            "fee_msat": payment.fee,
            "type": "paid_invoice",
            "fee": payment.fee / 1000,
            "value": int(payment.amount / 1000),
            "timestamp": payment.time,
            "memo": payment.extra.get("comment") or payment.memo if not payment.pending else "Payment in transition",
        }
        for payment in reversed(
            (
                await get_payments(
                    wallet_id=key_type.wallet.id,
                    pending=True,
                    complete=True,
                    outgoing=True,
                    incoming=False,
                    limit=limit,
                    offset=offset,
                )
            )
        )
    ]


@lndhub_api_router.get("/getuserinvoices")
async def lndhub_getuserinvoices(
    key_type: WalletTypeInfo = Depends(check_wallet),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return [
        {
            "r_hash": to_buffer(payment.payment_hash),
            "payment_request": payment.bolt11,
            "add_index": "500",
            "description": payment.extra.get("comment") or payment.memo,
            "payment_hash": payment.payment_hash,
            "ispaid": payment.success,
            "amt": int(payment.amount / 1000),
            "expire_time": int(time.time() + 1800),
            "timestamp": payment.time,
            "type": "user_invoice",
        }
        for payment in reversed(
            (
                await get_payments(
                    wallet_id=key_type.wallet.id,
                    pending=True,
                    complete=True,
                    incoming=True,
                    outgoing=False,
                    limit=limit,
                    offset=offset,
                )
            )
        )
    ]


@lndhub_api_router.get("/getbtc", dependencies=[Depends(check_wallet)])
async def lndhub_getbtc():
    "load an address for incoming onchain btc"
    return []


@lndhub_api_router.get("/getpending", dependencies=[Depends(check_wallet)])
async def lndhub_getpending():
    "pending onchain transactions"
    return []


@lndhub_api_router.get("/decodeinvoice")
async def lndhub_decodeinvoice(invoice: str):
    inv = bolt11_decode(invoice)
    return decoded_as_lndhub(inv)


@lndhub_api_router.get("/checkrouteinvoice")
async def lndhub_checkrouteinvoice():
    "not implemented on canonical lndhub"
