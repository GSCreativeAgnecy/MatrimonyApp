"""Settings validation: production fail-fast on insecure configuration."""

import pytest
from pydantic import ValidationError

from app.config.settings import Settings

STRONG_SECRET = "x" * 48


class TestProductionSafety:
    def test_development_allows_defaults(self):
        s = Settings(ENVIRONMENT="development")
        assert s.PAYMENT_PROVIDER == "mock"

    def test_production_rejects_default_jwt_secret(self):
        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="production",
                JWT_SECRET_KEY="change-me-in-production",
                PAYMENT_PROVIDER="stripe",
                PAYMENT_API_KEY="sk_test",
                PAYMENT_WEBHOOK_SECRET="whsec_real",
            )

    def test_production_rejects_short_jwt_secret(self):
        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="production",
                JWT_SECRET_KEY="short",
                PAYMENT_PROVIDER="stripe",
                PAYMENT_API_KEY="sk_test",
                PAYMENT_WEBHOOK_SECRET="whsec_real",
            )

    def test_production_rejects_mock_provider(self):
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="production", JWT_SECRET_KEY=STRONG_SECRET, PAYMENT_PROVIDER="mock")

    def test_production_allows_mock_provider_with_explicit_optin(self):
        s = Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY=STRONG_SECRET,
            PAYMENT_PROVIDER="mock",
            ALLOW_MOCK_PAYMENTS=True,
        )
        assert s.PAYMENT_PROVIDER == "mock"

    def test_production_stripe_requires_keys(self):
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="production", JWT_SECRET_KEY=STRONG_SECRET, PAYMENT_PROVIDER="stripe")

        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="production",
                JWT_SECRET_KEY=STRONG_SECRET,
                PAYMENT_PROVIDER="stripe",
                PAYMENT_API_KEY="sk_test",
                PAYMENT_WEBHOOK_SECRET="change-me-webhook-secret",
            )

    def test_production_stripe_with_keys_is_valid(self):
        s = Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY=STRONG_SECRET,
            PAYMENT_PROVIDER="stripe",
            PAYMENT_API_KEY="sk_test",
            PAYMENT_WEBHOOK_SECRET="whsec_real",
        )
        assert s.is_production

    def test_unknown_payment_provider_rejected(self):
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="development", PAYMENT_PROVIDER="razorpay")
