"""Phase 08 unit tests: core/errors.py — BedrockErrorCategory + ErrorClassifier.

Locks PORT_LOG #017: extraction from runtime/bedrock_client.py preserves
classification semantics byte-for-byte.
"""
from __future__ import annotations

import os
import sys

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_validation_cache_classified():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    exc = Exception("ValidationException: cache_control not supported in this region")
    cat, recovery, _ = ErrorClassifier.classify(exc)
    assert cat == BedrockErrorCategory.VALIDATION_CACHE
    assert recovery == "strip_cache_retry"


def test_context_overflow_classified():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    exc = Exception("ValidationException: prompt is too long")
    cat, recovery, _ = ErrorClassifier.classify(exc)
    assert cat == BedrockErrorCategory.CONTEXT_OVERFLOW
    assert recovery == "compact_retry"


def test_validation_other_no_retry():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    exc = Exception("ValidationException: unknown field 'foo'")
    cat, recovery, _ = ErrorClassifier.classify(exc)
    assert cat == BedrockErrorCategory.VALIDATION_OTHER
    assert recovery == "no_retry"


def test_throttle_classified():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    exc = Exception("ThrottlingException: rate exceeded")
    cat, recovery, _ = ErrorClassifier.classify(exc)
    assert cat == BedrockErrorCategory.THROTTLE
    assert recovery == "backoff"


def test_service_unavailable_classified():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    exc = Exception("ServiceUnavailable 503")
    cat, recovery, _ = ErrorClassifier.classify(exc)
    assert cat == BedrockErrorCategory.SERVICE_UNAVAILABLE
    assert recovery == "backoff"


def test_model_not_ready_classified():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    exc = Exception("ModelNotReady: not ready yet")
    cat, recovery, _ = ErrorClassifier.classify(exc)
    assert cat == BedrockErrorCategory.MODEL_NOT_READY
    assert recovery == "backoff"


def test_access_denied_no_retry():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    exc = Exception("AccessDenied: 403 Forbidden")
    cat, recovery, _ = ErrorClassifier.classify(exc)
    assert cat == BedrockErrorCategory.ACCESS_DENIED
    assert recovery == "no_retry"


def test_network_error_via_class_name():
    from core.errors import BedrockErrorCategory, ErrorClassifier

    class EndpointConnectionError(Exception):
        pass

    cat, recovery, _ = ErrorClassifier.classify(EndpointConnectionError("connection failed"))
    assert cat == BedrockErrorCategory.NETWORK
    assert recovery == "backoff"


def test_unknown_error_no_retry():
    from core.errors import BedrockErrorCategory, ErrorClassifier
    exc = Exception("something completely unexpected")
    cat, recovery, _ = ErrorClassifier.classify(exc)
    assert cat == BedrockErrorCategory.UNKNOWN
    assert recovery == "no_retry"


def test_debug_msg_truncated_to_200():
    from core.errors import ErrorClassifier
    big = "x" * 500
    exc = Exception(f"ValidationException: {big}")
    _, _, debug = ErrorClassifier.classify(exc)
    assert len(debug) <= 200


def test_runtime_bedrock_client_re_exports_match():
    """PORT_LOG #017 byte-equivalence: runtime.bedrock_client must re-export
    the exact same classes from core.errors so existing call-sites work."""
    from core.errors import BedrockErrorCategory as CoreCat, ErrorClassifier as CoreCls
    from runtime.bedrock_client import BedrockErrorCategory as RuntimeCat, ErrorClassifier as RuntimeCls
    assert CoreCat is RuntimeCat
    assert CoreCls is RuntimeCls
