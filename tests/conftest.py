import os

# Ensure required settings exist in environments without a .env file (CI, Docker test runs).
# These are overridden by real values in .env locally.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only-not-for-production")
