from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_enforce_data_retention_calls_rpc() -> None:
    rpc_calls: list[str] = []

    class _RpcResult:
        data = 3

    class _Chain:
        def rpc(self, name, *_args, **_kwargs):
            rpc_calls.append(name)
            return self

        def execute(self):
            return _RpcResult()

    with patch("app.tasks.scheduler.get_service_client", return_value=_Chain()):
        from app.tasks.scheduler import enforce_data_retention

        await enforce_data_retention()

    assert "apply_data_retention" in rpc_calls
