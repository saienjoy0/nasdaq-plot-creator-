import shutil
import tempfile
import unittest
from pathlib import Path

import test_memory_revalidation as base


class FinalHardeningTest(unittest.TestCase):
    def setUp(self):
        self.case = base.MemoryRevalidationBridgeTest(methodName="runTest")
        self.case.setUp()

    def tearDown(self):
        self.case.tearDown()

    def test_actual_without_current_evidence_fails(self):
        dossier = self.case.base_dossier()
        dossier["expected_actual_gap"]["actual"]["evidence_ids"] = []
        self.case.rewrite_dossier(dossier)
        self.assertTrue(
            any("Actual has a statement" in error for error in self.case.validate().errors)
        )

    def test_memory_evidence_is_rejected_even_when_mixed(self):
        dossier = self.case.base_dossier()
        dossier["evidence"][1]["source_reference"] = "memory:old-claim"
        self.case.rewrite_dossier(dossier)
        errors = self.case.validate().errors
        self.assertTrue(
            any("cannot be registered as current evidence" in error for error in errors)
        )
        self.assertTrue(any("causal edge cannot reference" in error for error in errors))

    def test_external_contracts_directory_fails(self):
        self.case.base_dossier()
        outside = Path(tempfile.mkdtemp(prefix="contracts-outside-"))
        try:
            result = base.validate_dossier(
                self.case.dossier,
                self.case.manifest,
                self.case.report,
                contracts_dir=outside,
                repo_root=base.ROOT,
                retrieval_runner=base.fake_retrieve,
            )
            self.assertTrue(
                any("contracts directory escapes" in error for error in result.errors)
            )
        finally:
            shutil.rmtree(outside)


if __name__ == "__main__":
    unittest.main()
