import pytest
import asyncio
from shared.utils.circuit_breaker import CircuitBreakerService, CircuitState

class TestCircuitBreaker:
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        cb = CircuitBreakerService(failure_threshold=3, recovery_timeout=5)
        
        async def successful_function():
            return "success"
        
        result = await cb.call(successful_function)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after failure threshold"""
        cb = CircuitBreakerService(failure_threshold=2, recovery_timeout=5)
        
        async def failing_function():
            raise Exception("Service unavailable")
        
        # First failure
        with pytest.raises(Exception):
            await cb.call(failing_function)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1
        
        # Second failure - should open circuit
        with pytest.raises(Exception):
            await cb.call(failing_function)
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks calls when open"""
        cb = CircuitBreakerService(failure_threshold=1, recovery_timeout=60)
        
        async def failing_function():
            raise Exception("Service unavailable")
        
        # Trigger circuit to open
        with pytest.raises(Exception):
            await cb.call(failing_function)
        assert cb.state == CircuitState.OPEN
        
        # Next call should be blocked
        async def any_function():
            return "should not execute"
        
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(any_function)

    def test_circuit_breaker_state_info(self):
        """Test circuit breaker state information"""
        cb = CircuitBreakerService(failure_threshold=5, recovery_timeout=30)
        
        state_info = cb.get_state()
        assert "state" in state_info
        assert "failure_count" in state_info
        assert "last_failure_time" in state_info
        assert state_info["state"] == "closed"
        assert state_info["failure_count"] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
