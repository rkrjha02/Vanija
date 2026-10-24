"""Tests for the customer lock with timeout. Uses the test database."""

import asyncio

import pytest
from sqlalchemy import text

from app.data.database import engine
from app.data.locking import LockTimeoutError, customer_lock


@pytest.fixture
async def held_lock():
    """Hold an advisory lock on a known customer ID for the duration of the test."""
    cid = "lock-test-customer"
    conn = await engine.connect()
    await conn.execute(text("SELECT pg_advisory_lock(hashtext(:cid))"), {"cid": cid})
    yield cid
    await conn.execute(text("SELECT pg_advisory_unlock(hashtext(:cid))"), {"cid": cid})
    await conn.close()


class TestLockTimeout:
    async def test_lock_acquired_normally(self, engine):
        """A lock with no contention is acquired immediately."""
        cid = "no-contention-customer"
        async with customer_lock(cid, timeout=2):
            pass

    async def test_timeout_raises_when_lock_held(self, held_lock):
        """A second caller times out while the lock is held."""
        with pytest.raises(LockTimeoutError):
            async with customer_lock(held_lock, timeout=1):
                pass

    async def test_lock_released_after_normal_use(self, engine):
        """After the context manager exits, the lock is released and reacquirable."""
        cid = "release-test-customer"
        async with customer_lock(cid, timeout=2):
            pass
        async with customer_lock(cid, timeout=2):
            pass

    async def test_lock_released_on_exception(self, engine):
        """The lock is released even when the body raises."""
        cid = "exception-test-customer"
        with pytest.raises(ValueError):
            async with customer_lock(cid, timeout=2):
                raise ValueError("boom")
        async with customer_lock(cid, timeout=2):
            pass

    async def test_timeout_does_not_save_message(self, held_lock):
        """The timed-out path should not create any side effects.
        We verify by checking that LockTimeoutError is raised before
        any code inside the context manager runs."""
        entered = False
        with pytest.raises(LockTimeoutError):
            async with customer_lock(held_lock, timeout=1):
                entered = True
        assert not entered, "The body should never execute on timeout"
