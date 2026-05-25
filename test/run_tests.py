# =====================================================================================
# Imports: External
# =====================================================================================
import os
import sys
import unittest
from pathlib import Path

# =====================================================================================
# MAIN - Discover and run tests
# =====================================================================================
if __name__ == "__main__":

    loader = unittest.TestLoader()

    # Build Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    framework_path = os.path.join(project_root, "recon-ngx")

    # Check paths are as expected
    if not os.path.isdir(framework_path):
        print("[!] ERROR: Could not find The Recon-NGX framework folder (recon-ngx).")
        print("[!] Make sure the recon-ngx project exists at the same level as the recon-ngx-marketplace")
        sys.exit(1)
    sys.path.append(framework_path)

    suite = loader.discover(
        start_dir="tests",
        pattern="test_*.py",
        top_level_dir="."
    )

    runner = unittest.TextTestRunner(
        verbosity=2
    )

    result = runner.run(suite)

    sys.exit(not result.wasSuccessful())