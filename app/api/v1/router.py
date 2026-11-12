"""Aggregated router for API version 1."""

# Third-party
from fastapi import APIRouter

# Project imports
from app.api.v1 import accounts, audit_logs, auth, transactions, transfers, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(accounts.router)
api_router.include_router(transfers.router)
api_router.include_router(transactions.router)
api_router.include_router(audit_logs.router)
