"""Shared test helpers for christiangeorgelucas/color-tools."""

import math

from gen.messages_pb2 import Color


class TestContext:
    """Minimal AxiomContext implementation for unit tests."""

    class _Logger:
        def debug(self, msg: str, **attrs) -> None: pass
        def info(self, msg: str, **attrs) -> None: pass
        def warn(self, msg: str, **attrs) -> None: pass
        def error(self, msg: str, **attrs) -> None: pass

    class _Secrets:
        def __init__(self, m: dict) -> None:
            self._m = m or {}

        def get(self, name: str):
            v = self._m.get(name)
            return (v, True) if v is not None else ("", False)

    def __init__(self, secrets_map: dict | None = None) -> None:
        self.log = self._Logger()
        self.secrets = self._Secrets(secrets_map or {})
        self.execution_id = "test-execution-id"
        self.flow_id = "test-flow-id"
        self.tenant_id = "test-tenant-id"


def ax() -> TestContext:
    return TestContext()


def color(space: str, *components) -> Color:
    return Color(space=space, components=list(components))


def srgb(r: float, g: float, b: float) -> Color:
    return Color(space="srgb", components=[r, g, b])


def assert_ok(result) -> None:
    assert not result.error.code, (
        f"unexpected error: {result.error.code}: {result.error.message}"
    )


def assert_error(result, code: str) -> None:
    assert result.error.code == code, (
        f"expected error {code}, got {result.error.code or '<none>'}: "
        f"{result.error.message}"
    )
    assert result.error.message, "an error must carry a human-readable message"


def close(actual: float, expected: float, rel: float = 1e-9, abs_: float = 1e-9) -> None:
    assert math.isclose(actual, expected, rel_tol=rel, abs_tol=abs_), (
        f"expected {expected!r}, got {actual!r} (abs diff {abs(actual - expected):.3e})"
    )
