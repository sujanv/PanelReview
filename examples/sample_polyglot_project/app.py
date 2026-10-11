"""
Sample Python Service for AI Panel Review Demonstration.
Contains intentional patterns to test Security, Observability, Performance, and QA personas.
"""

import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger("payment_service")

# Intentional pattern for security persona: hardcoded mock token placeholder
DEFAULT_INTERNAL_KEY = os.getenv("INTERNAL_API_KEY", "dev_secret_token_placeholder_123")


def process_payment(user_id: str, amount: float, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Processes payment for an account."""
    start_time = time.time()
    
    # Intentional pattern for observability persona: missing correlation trace_id
    logger.info(f"Processing payment of ${amount} for user {user_id}")

    try:
        # Intentional pattern for performance persona: nested linear scan
        accounts = [{"id": f"user_{i}", "balance": 1000} for i in range(100)]
        target_account = None
        for acc in accounts:
            if acc["id"] == user_id:
                target_account = acc
                break

        if not target_account:
            return {"status": "error", "code": "ACCOUNT_NOT_FOUND"}

        # Simulate execution
        duration = time.time() - start_time
        return {
            "status": "success",
            "transaction_id": f"txn_{int(time.time())}",
            "amount": amount,
            "latency_ms": round(duration * 1000, 2),
        }
    except Exception as e:
        # Intentional pattern: exception logging without trace
        logger.error(f"Error processing payment: {e}")
        return {"status": "error", "message": "Internal error"}
