"""Tests for resilience patterns."""

import pytest

from kubeflow_mcp.core.resilience import (
    CircuitBreaker,
    CircuitState,
    RateLimiter,
    retry_with_backoff,
    with_circuit_breaker,
)


def test_circuit_breaker_starts_closed():
    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute()


def test_circuit_breaker_opens_on_failures():
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.can_execute()

    for _ in range(3):
        cb.record_failure()

    assert cb.state == CircuitState.OPEN
    assert not cb.can_execute()


def test_circuit_breaker_success_resets_count():
    cb = CircuitBreaker(failure_threshold=3)

    cb.record_failure()
    cb.record_failure()
    cb.record_success()

    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED


def test_rate_limiter_allows_under_limit():
    rl = RateLimiter(rate=10, capacity=10)
    for _ in range(5):
        assert rl.acquire()


def test_rate_limiter_blocks_over_limit():
    rl = RateLimiter(rate=1, capacity=2)
    assert rl.acquire()
    assert rl.acquire()
    assert not rl.acquire()


def test_retry_with_backoff_succeeds():
    call_count = 0

    @retry_with_backoff(max_retries=3, base_delay=0.01)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert call_count == 3


def test_retry_with_backoff_exhausted():
    @retry_with_backoff(max_retries=2, base_delay=0.01)
    def always_fails():
        raise ValueError("Permanent error")

    with pytest.raises(ValueError, match="Permanent error"):
        always_fails()


def test_with_circuit_breaker_decorator():
    cb = CircuitBreaker(failure_threshold=2)
    call_count = 0

    @with_circuit_breaker(cb)
    def failing_function():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("fail")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            failing_function()

    assert cb.state == CircuitState.OPEN

    with pytest.raises(RuntimeError, match="Circuit breaker open"):
        failing_function()

    assert call_count == 2
