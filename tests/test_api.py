import asyncio
from base64 import urlsafe_b64encode
from uuid import uuid4

import pytest
from bolt11 import decode as bolt11_decode
from httpx import AsyncClient
from lnbits.core.models.users import Account
from lnbits.core.services import create_invoice, pay_invoice, update_wallet_balance
from lnbits.core.services.users import create_user_account_no_ckeck
from lnbits.tasks import internal_invoice_queue

from ..decorators import sanitize_token


async def _user_with_wallet(username: str):
    account = Account(id=uuid4().hex, username=username)
    user = await create_user_account_no_ckeck(account=account)
    return user, user.wallets[0]


async def _drain_internal_invoice_queue() -> None:
    while True:
        try:
            internal_invoice_queue.get_nowait()
        except asyncio.QueueEmpty:
            return


async def _lndhub_headers(client: AsyncClient, login: str, password: str):
    auth = await client.post(
        "/lndhub/ext/auth",
        json={"login": login, "password": password},
    )
    assert auth.status_code == 200
    token = auth.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_sanitize_token_decodes_lndhub_bearer_token():
    token = urlsafe_b64encode(b"admin:admin-key").decode("ascii")

    assert await sanitize_token(f"Bearer {token}") == "admin-key"


@pytest.mark.asyncio
async def test_lndhub_addinvoice_with_expiry(client: AsyncClient):
    _user, wallet = await _user_with_wallet("lhaddexpiry")
    headers = await _lndhub_headers(client, "invoice", wallet.inkey)

    response = await client.post(
        "/lndhub/ext/addinvoice",
        json={"amt": 21, "memo": "expiry invoice", "expiry": 600},
        headers=headers,
    )

    assert response.status_code == 200
    invoice = response.json()
    assert invoice["expiry"] == 600
    decoded = bolt11_decode(invoice["payment_request"])
    assert decoded.expiry == 600


@pytest.mark.asyncio
async def test_lndhub_addinvoice_without_expiry(client: AsyncClient):
    _user, wallet = await _user_with_wallet("lhaddnoexp")
    headers = await _lndhub_headers(client, "invoice", wallet.inkey)

    response = await client.post(
        "/lndhub/ext/addinvoice",
        json={"amt": 21, "memo": "default expiry invoice"},
        headers=headers,
    )

    assert response.status_code == 200
    invoice = response.json()
    assert invoice["expiry"] is None
    decoded = bolt11_decode(invoice["payment_request"])
    assert decoded.expiry


@pytest.mark.asyncio
async def test_lndhub_addinvoice_rejects_invalid_expiry(client: AsyncClient):
    _user, wallet = await _user_with_wallet("lhaddbadexp")
    headers = await _lndhub_headers(client, "invoice", wallet.inkey)

    response = await client.post(
        "/lndhub/ext/addinvoice",
        json={"amt": 21, "memo": "bad expiry invoice", "expiry": "invalid"},
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_lndhub_gettxs_returns_real_outgoing_payments(client: AsyncClient):
    await _drain_internal_invoice_queue()
    _payer_user, payer_wallet = await _user_with_wallet("lhpayer")
    _receiver_user, receiver_wallet = await _user_with_wallet("lhreceiver")
    headers = await _lndhub_headers(client, "admin", payer_wallet.adminkey)

    await update_wallet_balance(payer_wallet, 100_000)
    await _drain_internal_invoice_queue()

    outgoing = []
    for amount in (21, 34):
        invoice = await create_invoice(
            wallet_id=receiver_wallet.id,
            amount=amount,
            memo=f"lndhub receive {amount}",
            internal=True,
            extra={"tag": "lndhub-test"},
        )
        payment = await pay_invoice(
            wallet_id=payer_wallet.id,
            payment_request=invoice.bolt11,
            extra={"tag": "lndhub-test"},
        )
        outgoing.append(payment)
    await _drain_internal_invoice_queue()

    response = await client.get("/lndhub/ext/gettxs?limit=100", headers=headers)

    assert response.status_code == 200
    transactions = response.json()
    assert len(transactions) == 2
    assert {tx["payment_hash"] for tx in transactions} == {
        payment.payment_hash for payment in outgoing
    }
    assert {tx["value"] for tx in transactions} == {-21, -34}
    assert all(tx["type"] == "paid_invoice" for tx in transactions)


@pytest.mark.asyncio
async def test_lndhub_getuserinvoices_returns_real_incoming_payments(
    client: AsyncClient,
):
    await _drain_internal_invoice_queue()
    _payer_user, payer_wallet = await _user_with_wallet("lhpayerinv")
    _receiver_user, receiver_wallet = await _user_with_wallet("lhreceiverinv")
    headers = await _lndhub_headers(client, "invoice", receiver_wallet.inkey)

    await update_wallet_balance(payer_wallet, 100_000)
    await _drain_internal_invoice_queue()

    invoices = []
    for amount in (21, 34):
        invoice = await create_invoice(
            wallet_id=receiver_wallet.id,
            amount=amount,
            memo=f"lndhub receive {amount}",
            internal=True,
            extra={"tag": "lndhub-test"},
        )
        await pay_invoice(wallet_id=payer_wallet.id, payment_request=invoice.bolt11)
        invoices.append(invoice)
    await _drain_internal_invoice_queue()

    response = await client.get(
        "/lndhub/ext/getuserinvoices?limit=100", headers=headers
    )

    assert response.status_code == 200
    user_invoices = response.json()
    assert len(user_invoices) == 2
    assert {invoice["payment_hash"] for invoice in user_invoices} == {
        invoice.payment_hash for invoice in invoices
    }
    assert {invoice["amt"] for invoice in user_invoices} == {21, 34}
    assert all(invoice["ispaid"] is True for invoice in user_invoices)


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="/gettxs currently filters outgoing payments only, so incoming payments "
    "are only visible via /getuserinvoices."
)
async def test_lndhub_gettxs_includes_real_incoming_payments_for_clients(
    client: AsyncClient,
):
    await _drain_internal_invoice_queue()
    _payer_user, payer_wallet = await _user_with_wallet("lhpayerreg")
    _receiver_user, receiver_wallet = await _user_with_wallet("lhreceiverreg")
    headers = await _lndhub_headers(client, "invoice", receiver_wallet.inkey)

    await update_wallet_balance(payer_wallet, 100_000)
    await _drain_internal_invoice_queue()

    invoices = []
    for amount in (21, 34):
        invoice = await create_invoice(
            wallet_id=receiver_wallet.id,
            amount=amount,
            memo=f"lndhub receive {amount}",
            internal=True,
            extra={"tag": "lndhub-test"},
        )
        await pay_invoice(wallet_id=payer_wallet.id, payment_request=invoice.bolt11)
        invoices.append(invoice)
    await _drain_internal_invoice_queue()

    response = await client.get("/lndhub/ext/gettxs?limit=100", headers=headers)

    assert response.status_code == 200
    transactions = response.json()
    assert len(transactions) == 2
    assert {tx["payment_hash"] for tx in transactions} == {
        invoice.payment_hash for invoice in invoices
    }
