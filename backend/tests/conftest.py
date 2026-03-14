"""Test configuration and fixtures."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.dependencies import get_fbr_service
from app.services.mock_fbr_service import MockFBRService, MockBehavior


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_fbr_service() -> MockFBRService:
    """
    Configurable mock FBR service for testing.
    
    Example:
        def test_something(mock_fbr_service):
            mock_fbr_service.configure(MockBehavior.AUTH_ERROR)
            # ... test code ...
    """
    return MockFBRService()


@pytest_asyncio.fixture
async def client_with_mock_fbr(
    mock_fbr_service: MockFBRService,
) -> AsyncGenerator[tuple[AsyncClient, MockFBRService], None]:
    """
    Async HTTP client with mocked FBR service.
    
    Returns a tuple of (client, mock_service) so tests can configure
    the mock behavior and make assertions on call history.
    
    Example:
        async def test_submit_success(client_with_mock_fbr):
            client, mock_fbr = client_with_mock_fbr
            mock_fbr.configure(MockBehavior.SUCCESS)
            response = await client.post("/invoices/123/submit", ...)
            assert mock_fbr.call_count == 1
    """
    # Override the FBR service dependency
    app.dependency_overrides[get_fbr_service] = lambda: mock_fbr_service
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, mock_fbr_service
    
    # Clean up override
    app.dependency_overrides.clear()
