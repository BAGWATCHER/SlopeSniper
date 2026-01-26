"""Tests for intent storage functionality."""

import pytest
import time
from datetime import datetime, timezone

from slopesniper_skill.tools.intents import (
    create_intent,
    get_intent,
    mark_executed,
    list_pending_intents,
    get_intent_time_remaining,
    cleanup_expired,
    INTENT_TTL_SECONDS,
)


# Test data
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class TestIntentCreation:
    """Tests for intent creation."""

    def test_create_intent_returns_uuid(self) -> None:
        intent_id = create_intent(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount="1.0",
            slippage_bps=50,
            out_amount_est="100.0",
            unsigned_tx="base64encodedtx==",
            request_id="test-request-123",
        )
        assert intent_id is not None
        assert len(intent_id) == 36  # UUID format

    def test_create_intent_can_be_retrieved(self) -> None:
        intent_id = create_intent(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount="2.5",
            slippage_bps=100,
            out_amount_est="250.0",
            unsigned_tx="anothertx==",
            request_id="test-request-456",
        )

        intent = get_intent(intent_id)
        assert intent is not None
        assert intent.intent_id == intent_id
        assert intent.from_mint == SOL_MINT
        assert intent.to_mint == USDC_MINT
        assert intent.amount == "2.5"
        assert intent.slippage_bps == 100
        assert intent.executed is False


class TestIntentRetrieval:
    """Tests for intent retrieval."""

    def test_get_nonexistent_intent_returns_none(self) -> None:
        intent = get_intent("nonexistent-uuid-1234-5678-901234567890")
        assert intent is None

    def test_get_intent_includes_expiry(self) -> None:
        intent_id = create_intent(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount="1.0",
            slippage_bps=50,
            out_amount_est="100.0",
            unsigned_tx="tx==",
            request_id="req-123",
        )

        intent = get_intent(intent_id)
        assert intent is not None
        assert intent.expires_at > intent.created_at


class TestIntentExecution:
    """Tests for marking intents as executed."""

    def test_mark_executed_prevents_reuse(self) -> None:
        intent_id = create_intent(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount="1.0",
            slippage_bps=50,
            out_amount_est="100.0",
            unsigned_tx="tx==",
            request_id="req-123",
        )

        # First execution should succeed
        success = mark_executed(intent_id)
        assert success is True

        # Verify intent is marked as executed
        intent = get_intent(intent_id)
        assert intent is not None
        assert intent.executed is True

        # Second execution should fail
        success = mark_executed(intent_id)
        assert success is False

    def test_mark_nonexistent_intent_returns_false(self) -> None:
        success = mark_executed("nonexistent-uuid-1234-5678-901234567890")
        assert success is False


class TestIntentTimeRemaining:
    """Tests for time remaining calculation."""

    def test_new_intent_has_time_remaining(self) -> None:
        intent_id = create_intent(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount="1.0",
            slippage_bps=50,
            out_amount_est="100.0",
            unsigned_tx="tx==",
            request_id="req-123",
        )

        intent = get_intent(intent_id)
        assert intent is not None

        remaining = get_intent_time_remaining(intent)
        assert remaining > 0
        assert remaining <= INTENT_TTL_SECONDS


class TestPendingIntents:
    """Tests for listing pending intents."""

    def test_list_pending_intents(self) -> None:
        # Create a few intents
        intent_id1 = create_intent(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount="1.0",
            slippage_bps=50,
            out_amount_est="100.0",
            unsigned_tx="tx1==",
            request_id="req-1",
        )
        intent_id2 = create_intent(
            from_mint=USDC_MINT,
            to_mint=SOL_MINT,
            amount="100.0",
            slippage_bps=50,
            out_amount_est="1.0",
            unsigned_tx="tx2==",
            request_id="req-2",
        )

        pending = list_pending_intents()
        intent_ids = [i.intent_id for i in pending]

        assert intent_id1 in intent_ids
        assert intent_id2 in intent_ids

    def test_executed_intents_not_in_pending(self) -> None:
        intent_id = create_intent(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount="1.0",
            slippage_bps=50,
            out_amount_est="100.0",
            unsigned_tx="tx==",
            request_id="req-123",
        )

        # Mark as executed
        mark_executed(intent_id)

        pending = list_pending_intents()
        intent_ids = [i.intent_id for i in pending]

        assert intent_id not in intent_ids
