"""
src/examples/ex31_circuit_breaker.py

Implement circuit breaker to prevent cascading failures
"""

from typing import TypedDict
import time
import random
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class CircuitState(Enum):
    CLOSED  = "closed" # Normal operation
    OPEN = "open" # Failing, block requests
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    """Circuit breaker for external service calls"""

    def __init__(
        self, 
        failure_threshold: int = 3,
        recovery_timeout: int = 60, 
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold # exlpain self is the instance of the class we are currently using.
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    # ------------------------------------------------------------

    def call (self, func, *args, **kwargs):
        # explain args and kwargs are the arguments passed to the function.
        # explain that : *args is a tuple of arguments, **kwargs is a dictionary of arguments.
        """Execute function through circuit breaker""" 

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                print ("⚡ Circuit breaker: HALF_OPEN (testing recovery)")

            else :
                if self.last_failure_time is not None:
                    time_since_failure = time.time() - self.last_failure_time
                    wait_time = self.recovery_timeout - time_since_failure
                else:
                    wait_time = self.recovery_timeout
                raise Exception(
                    f"Circuit breaker OPEN."
                    f"Try again in {wait_time:.0f} seconds."
                )
        
        try : 
            result = func(*args, **kwargs)

            # Success - reset circuit breaker
            if self.state == CircuitState.HALF_OPEN:
                print ("✓ Circuit breaker: CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            
            return result
        except self.expected_exception:
            self.failure_count +=1
            self.last_failure_time = time.time()
            print (f"⚠ Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}")

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                print (f"⛔ Circuit breaker: OPEN (too many failures)")
            raise
    # ------------------------------------------------------------

    def _should_attempt_reset(self) -> bool:
        """ Check if enough time has passed to test recovery """
        if self.last_failure_time is None:
            return False
        return (
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    # ------------------------------------------------------------

# Usage in workflow
class ServiceState(TypedDict):
    data : str
    result : str
    circuit_breaker_status : str

# Create circuit breaker for LLM service
llm_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30
)

def call_llm_service(state: ServiceState) -> ServiceState:
    """ Call LLM service through circuit breaker """

    def flaky_llm_call():
        """Simulate a flaky LLM service call"""
        # Simulate flaky service - 50% chance of failure
        if random.random() < 0.5:
            raise Exception("LLM API error")
        return "Generated requirements from LLM"

    try :
        result = llm_circuit_breaker.call(flaky_llm_call)

        return {
            "result": result,
            "circuit_breaker_status": llm_circuit_breaker.state.value,
            "data": state["data"]
        }
    except Exception as e:
        return {
            "result": f"Error: {str(e)}",
            "circuit_breaker_status": llm_circuit_breaker.state.value,
            "data": state["data"]
        }

# ------------------------------------------------------------

# Test Circuit Breaker
print ("=== Testing Circuit Breaker ===")
for i in range(10):
    state: ServiceState = {"data": "test", "result": "", "circuit_breaker_status": ""}
    result = call_llm_service(state)
    
    print (f"Request {i+1}:")
    print (f"  Result: {result['result'][:50]}")
    print (f"  Circuit: {result['circuit_breaker_status']}")
    print ()
    time.sleep(2)
    
