from __future__ import annotations

import unittest

from tracecontract.security import prepare_retrieval, prepare_inference_context
from tracecontract import PolicyError


class SecurityBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifact = {
            "id": "CODE-1", "project_id": "p1", "classification": "confidential",
            "acl": ["developer:1"], "content": {"source": "secret implementation"},
        }

    def test_acl_is_enforced_before_retrieval(self) -> None:
        with self.assertRaisesRegex(PolicyError, "access denied"):
            prepare_retrieval([self.artifact], "developer:2", "p1")
        self.assertEqual([self.artifact], prepare_retrieval([self.artifact], "developer:1", "p1"))

    def test_cloud_context_is_allowlisted_minimized_and_audited_by_hash(self) -> None:
        prepared = prepare_inference_context(
            [self.artifact], provider="approved-cloud", model="model-v1",
            provider_allowlist={"approved-cloud": "confidential"},
            prompt_id="review-v1", configuration={"temperature": 0},
        )
        self.assertEqual([{"id": "CODE-1", "content": {"source": "secret implementation"}}], prepared["context"])
        self.assertNotIn("secret", str(prepared["audit"]))
        self.assertEqual(64, len(prepared["audit"]["context_hash"]))
        with self.assertRaisesRegex(PolicyError, "provider is not allowlisted"):
            prepare_inference_context([self.artifact], "other-cloud", "m", {}, "p", {})


if __name__ == "__main__":
    unittest.main()
