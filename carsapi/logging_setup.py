# carsapi/logging_setup.py
import logging
import os
import structlog

def setup_logging():
    is_dev = os.getenv("DEBUG", "false").lower() == "true"
    processors = [structlog.processors.TimeStamper(fmt="iso")]
    processors += [structlog.dev.ConsoleRenderer()] if is_dev else [structlog.processors.JSONRenderer()]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
    )

setup_logging()
