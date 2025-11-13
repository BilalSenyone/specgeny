"""
Exercise 9: Production-Ready Requirement Extractor

Build fault-tolerant extraction with comprehensive error handling
"""

from enum import Enum
from time import time
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field, ValidationError

# TODO: Define Requirement model with validation

# TODO: Define state
class ProductionState(TypedDict):
    user_input: str
    requirements: List[dict]
    errors: List[str]
    retry_count: int
    circuit_breaker_open: bool
    fallback_used: bool
    prompt_complexity: str  # "complex", "simple", "minimal"

class CircuitState(Enum):
    CLOSED  = "closed" # Normal operation
    OPEN = "open" # Failing, block requests
    HALF_OPEN = "half_open" # Testing recovery

# TODO Implement circuit breaker class

class CircuitBraker :
    """Circuit breaker for external service calls"""

    # Init only called once when the object is created, not when the method is called.
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60, expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        # Initialize failure count and last failure time
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        # ------------------------------------------------------------
    
    def call (self, func, *arg, **kwargs):
        """ Execute function through circuit breaker """
        #If OPEN, check if we should attempt a reset (> HALF_OPEN)
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                print ("⚡ Circuit breaker: HALF_OPEN (testing recovery)")
        
            else : # Shouldn't attempt reset yet, wait for recovery timeout
                if self.last_failure_time is not None : 
                    time_since_failure = time.time() - self.last_failure_time
                    wait_time = self.recovery_timeout - time_since_failure
                else : 
                    wait_time = self.recovery_timeout
                raise Exception(
                    f"Circuit breaker OPEN."
                    f"Try again in {wait_time:.0f} seconds."
                )
        
        try : 
            # Call the function through the circuit breaker
            result = func(*arg, **kwargs)

            # Success - reset circuit breaker
            if self.state == CircuitState.HALF_OPEN:
                print ("✓ Circuit breaker: HALF OPEN (recovered) > CLOSED (no more failures)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

            return result
        except self.expected_exception as e: 
            self.failure_count += 1
            self.last_failure_time = time.time()
            print (f"⚠ Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}")

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN # Too many failures, open the circuit breaker
                print (f"⛔ Circuit breaker: OPEN (too many failures). Blocking requests.")
            raise
    # ------------------------------------------------------------

    def _should_attempt_reset(self) -> bool:
        """ Check if enough time has passed to test recovery """
        if self.last_failure_time is None:
            return False
        
        return(
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    # ------------------------------------------------------------

# TODO: Implement retry decorator
