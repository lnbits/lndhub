from fastapi import Query
from pydantic import BaseModel


class LndhubCreateInvoice(BaseModel):
    invoice: str = Query(...)


class LndhubAddInvoice(BaseModel):
    amt: int = Query(...)
    memo: str = Query(...)
    preimage: str = Query(None)


class LndhubAuthData(BaseModel):
    login: str = Query(None)
    password: str = Query(None)
    refresh_token: str = Query(None)
