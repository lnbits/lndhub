from fastapi import Query
from pydantic import BaseModel


class LndhubCreateInvoice(BaseModel):
    invoice: str = Query(...)


class LndhubAddInvoice(BaseModel):
    amt: int = Query(...)
    memo: str = Query(...)
    preimage: str | None = Query(None)


class LndhubAuthData(BaseModel):
    login: str | None = Query(None)
    password: str | None = Query(None)
    refresh_token: str | None = Query(None)
