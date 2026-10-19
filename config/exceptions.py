"""Consistent JSON error responses for the whole API."""
import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wrap DRF's default handler so every error looks like:

        {"error": {"status_code": 400, "message": "...", "details": {...}}}
    """
    response = exception_handler(exc, context)

    # Database constraint violations that slipped past serializer validation.
    if response is None and isinstance(exc, IntegrityError):
        logger.warning("IntegrityError: %s", exc)
        return Response(
            {
                "error": {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "A database constraint was violated (duplicate or invalid reference).",
                    "details": {},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if response is None:
        # Unhandled exception: let Django return its own 500 response.
        return None

    details = response.data
    if isinstance(details, dict) and "detail" in details and len(details) == 1:
        message = str(details["detail"])
        details = {}
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        message = "Validation failed."
    else:
        message = "Request failed."

    response.data = {
        "error": {
            "status_code": response.status_code,
            "message": message,
            "details": details,
        }
    }
    return response
