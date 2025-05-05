from base64 import urlsafe_b64encode

from bolt11 import decode as bolt11_decode
from fastapi import APIRouter, Depends, Query
from lnbits.core.crud import get_payments
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import create_invoice, pay_invoice
from lnbits.settings import settings

from .decorators import lndhub_require_admin_key, lndhub_require_invoice_key
from .models import LndhubAddInvoice, LndhubAuthData, LndhubCreateInvoice
from .utils import decoded_as_lndhub, to_buffer

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
    data: LndhubAddInvoice, wallet: WalletTypeInfo = Depends(lndhub_require_invoice_key)
):
    payment = await create_invoice(
        wallet_id=wallet.wallet.id,
        amount=data.amt,
        memo=data.memo or settings.lnbits_site_title,
        extra={"tag": "lndhub"},
    )
    return {
        "pay_req": payment.bolt11,  # client backwards compatibility
        "payment_request": payment.bolt11,
        "add_index": "500",
        "r_hash": to_buffer(payment.payment_hash),
        "hash": payment.payment_hash,
    }


@lndhub_api_router.post("/payinvoice")
async def lndhub_payinvoice(
    r_invoice: LndhubCreateInvoice,
    key_type: WalletTypeInfo = Depends(lndhub_require_admin_key),
):
    try:
        invoice = bolt11_decode(r_invoice.invoice)
    except Exception:
        return {"payment_error": "Invalid invoice"}
    try:
        payment = await pay_invoice(
            wallet_id=key_type.wallet.id,
            payment_request=r_invoice.invoice,
            extra={"tag": "lndhub"},
        )
    except Exception:
        return {"payment_error": "Payment failed"}

    return {
        "payment_error": "",
        "payment_preimage": payment.preimage,
        "route": {},
        "payment_hash": invoice.payment_hash,
        "decoded": decoded_as_lndhub(invoice),
        "fee_msat": payment.fee,
        "type": "paid_invoice",
        "fee": int(payment.fee / 1000),
        "value": invoice.amount_msat / 1000 if invoice.amount_msat else 0,
        "timestamp": payment.time.timestamp(),
        "memo": invoice.description,
    }


@lndhub_api_router.get("/balance")
async def lndhub_balance(
    key_type: WalletTypeInfo = Depends(lndhub_require_invoice_key),
):
    return {"BTC": {"AvailableBalance": key_type.wallet.balance}}


@lndhub_api_router.get("/gettxs")
async def lndhub_gettxs(
    key_type: WalletTypeInfo = Depends(lndhub_require_invoice_key),
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
            "timestamp": int(payment.time.timestamp()),
            "memo": (
                payment.extra and payment.extra.get("comment") or payment.memo
                if not payment.pending
                else "Payment in transition"
            ),
        }
        for payment in reversed(
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
    ]


@lndhub_api_router.get("/getuserinvoices")
async def lndhub_getuserinvoices(
    key_type: WalletTypeInfo = Depends(lndhub_require_invoice_key),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return [
        {
            "r_hash": to_buffer(payment.payment_hash),
            "payment_request": payment.bolt11,
            "add_index": "500",
            "description": (
                (payment.extra and payment.extra.get("comment")) or payment.memo
            ),
            "payment_hash": payment.payment_hash,
            "ispaid": payment.success,
            "amt": int(payment.amount / 1000),
            "expire_time": (
                int(payment.expiry.timestamp())
                if payment.expiry
                else payment.time.timestamp() + 3600
            ),
            "timestamp": int(payment.time.timestamp()),
            "type": "user_invoice",
        }
        for payment in reversed(
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
    ]


@lndhub_api_router.get("/getbtc", dependencies=[Depends(lndhub_require_invoice_key)])
async def lndhub_getbtc():
    "load an address for incoming onchain btc"
    return []


@lndhub_api_router.get(
    "/getpending", dependencies=[Depends(lndhub_require_invoice_key)]
)
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
