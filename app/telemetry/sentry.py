import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration


def init_sentry(dsn: str, environment: str = "development") -> None:
    """Initialize Sentry SDK. No-op when DSN is not configured."""
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=1.0,
        environment=environment,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
    )


def capture_exception(exc: Exception) -> None:
    """Capture an exception to Sentry. No-op when Sentry is not initialized."""
    sentry_sdk.capture_exception(exc)
