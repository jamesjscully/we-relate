"""
Phoenix tracing configuration for We-Relate application.
This module provides a centralized way to set up and manage Phoenix tracing.
"""

import os
import logging
from typing import Optional
from phoenix.otel import register
from opentelemetry import trace

logger = logging.getLogger(__name__)

class PhoenixConfig:
    """Configuration class for Phoenix tracing"""
    
    def __init__(self):
        self.project_name = "we-relate"
        self.endpoint = os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006/v1/traces")
        self.auto_instrument = True
        self.enabled = os.getenv("PHOENIX_TRACING_ENABLED", "true").lower() == "true"
        self.tracer_provider: Optional[trace.TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None

    def setup_tracing(self) -> bool:
        """
        Set up Phoenix tracing for the application.
        Returns True if successful, False otherwise.
        """
        if not self.enabled:
            logger.info("Phoenix tracing is disabled")
            return False
        
        try:
            logger.info(f"Setting up Phoenix tracing for project: {self.project_name}")
            logger.info(f"Phoenix endpoint: {self.endpoint}")
            
            self.tracer_provider = register(
                project_name=self.project_name,
                auto_instrument=self.auto_instrument,
                endpoint=self.endpoint,
                set_global_tracer_provider=True  # Make this the global tracer
            )
            
            self.tracer = self.tracer_provider.get_tracer(__name__)
            logger.info("Phoenix tracing setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up Phoenix tracing: {e}")
            return False

    def get_tracer(self) -> Optional[trace.Tracer]:
        """Get the configured tracer"""
        return self.tracer

    def is_enabled(self) -> bool:
        """Check if tracing is enabled"""
        return self.enabled and self.tracer is not None

# Global configuration instance
phoenix_config = PhoenixConfig()

def setup_phoenix_tracing() -> bool:
    """
    Convenience function to set up Phoenix tracing.
    Call this once at application startup.
    """
    return phoenix_config.setup_tracing()

def get_tracer() -> Optional[trace.Tracer]:
    """
    Get the Phoenix tracer for manual span creation.
    Returns None if tracing is not enabled.
    """
    return phoenix_config.get_tracer()

def trace_function(name: str):
    """
    Decorator to trace a function.
    Usage: @trace_function("my_function_name")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not phoenix_config.is_enabled():
                return func(*args, **kwargs)
            
            tracer = get_tracer()
            if not tracer:
                return func(*args, **kwargs)
            
            with tracer.start_as_current_span(name) as span:
                try:
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Add result metadata if it's a simple type
                    if isinstance(result, (str, int, float, bool)):
                        span.set_attribute("function.result", str(result))
                    
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator

def add_span_attributes(**attributes):
    """
    Add custom attributes to the current span.
    Usage: add_span_attributes(user_id="123", conversation_id="abc")
    """
    if not phoenix_config.is_enabled():
        return
    
    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, str(value))

# Example usage functions for the We-Relate app
def trace_coach_response(func):
    """Specific decorator for coach response functions"""
    def wrapper(*args, **kwargs):
        if not phoenix_config.is_enabled():
            return func(*args, **kwargs)
        
        tracer = get_tracer()
        if not tracer:
            return func(*args, **kwargs)
        
        with tracer.start_as_current_span("coach_response") as span:
            span.set_attribute("component", "coach")
            span.set_attribute("function_name", func.__name__)
            
            try:
                result = func(*args, **kwargs)
                if isinstance(result, str):
                    span.set_attribute("response_length", len(result))
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    
    return wrapper

def trace_partner_response(func):
    """Specific decorator for partner response functions"""
    def wrapper(*args, **kwargs):
        if not phoenix_config.is_enabled():
            return func(*args, **kwargs)
        
        tracer = get_tracer()
        if not tracer:
            return func(*args, **kwargs)
        
        with tracer.start_as_current_span("partner_response") as span:
            span.set_attribute("component", "partner")
            span.set_attribute("function_name", func.__name__)
            
            try:
                result = func(*args, **kwargs)
                if isinstance(result, str):
                    span.set_attribute("response_length", len(result))
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    
    return wrapper 