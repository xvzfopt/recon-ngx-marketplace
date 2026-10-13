# =====================================================================================
# Imports: External
# =====================================================================================
import os

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.sdk.exceptions import *
from module_test_case import ModuleTestCase

# =====================================================================================
# GitHub Dorks Analyzer Module Test Case Class
# =====================================================================================
class TestGitHubDorksAnalyzer(ModuleTestCase):
    '''
    Tests the GitHub Dorks Analyzer Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "recon/repositories-vulnerabilities/github_dorks_analyzer"
    TEST_RESULTS_FILENAME   = "test_results.json"
    TMP_DORKS_FILE          = os.path.join(ModuleTestCase.TMP_PATH, "tmp_dorks_file.txt")
    TEST_REPO               = "xvzfopt/recon-ngx"
    TEST_DORK               = "extension:py import sqlite3"

    # =====================================================================================
    # General Methods
    # =====================================================================================
    def setUp(self):
        super().setUp()

        # Set up Recon-NGX App
        self.set_up_recon_ngx()

        # Build Modules Paths
        mod_file_path = os.path.join(self.MODULES_PATH, self.FQN)

        # Load Module
        self._module = self.load_module(self.FQN, mod_file_path)
        self._module.THROTTLE_DURATION = 0

        # Misc Props
        self.test_results_path = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_FILENAME)

        # Write Test Dorks
        self._create_tmp_dorks_file([
            self.TEST_DORK
        ])
        self._module.get_options()["DorksFile"] = self.TMP_DORKS_FILE

    # =====================================================================================
    # Unit tests
    # =====================================================================================
    def test_successful_run(self):
        '''
        Tests successful execution of the Module
        '''

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()

        # Check initial Database state
        vulns = self.get_table_rows("vulnerabilities")
        self.assertEmpty(vulns)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        # Check Output
        self.assertInOutput(r".*Query \(1 of 1\).*")
        self.assertInOutput(r".*Vulnerabilities discovered: 4")
        self.assertInOutput(r".*Repositories processed: 1")

        # Check actual DB entries
        vulns = self.get_table_rows("vulnerabilities", True)
        self.assertLengthEqual(vulns, 4)

        self.assertEqual(vulns[0]["category"], "github_dork")
        self.assertEqual(vulns[0]["example"], "https://github.com/xvzfopt/recon-ngx/blob/f997e605a2fc513d6b0d4fba83979797e7dc60fd/recon/core/db/db.py")
        self.assertEqual(vulns[0]["reference"], f"repo:{self.TEST_REPO} {self.TEST_DORK}")

        self.assertEqual(vulns[2]["category"], "github_dork")
        self.assertEqual(vulns[2]["example"], "https://github.com/xvzfopt/recon-ngx/blob/f997e605a2fc513d6b0d4fba83979797e7dc60fd/recon/core/interpreter/base.py")
        self.assertEqual(vulns[2]["reference"], f"repo:{self.TEST_REPO} {self.TEST_DORK}")

    def test_run_failures(self):
        '''
        Tests failure runs of the module
        '''

        # Set options
        self._recon.set_verbosity(1)
        self._module.THROTTLE_DURATION = 6

        # Set Up Module
        self._recon.validate_options(self._module)
        self._module.preflight()

        # =====================================================================================
        # Test - Bad URL
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = URL.replace(".com", ".com/blah")

        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_REPO])
        self.assertExceptionStringEqual("Unexpected response when trying to perform a GitHub search: 404", cm)
        self._module.BASE_URL = URL

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = URL.replace(".com", ".fdsfsd")

        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_REPO])
        self.assertStartsWith(str(cm.exception), "Unable to reach GitHub API: ")

    def test_invalid_api_key(self):
        '''
        Test Handling of connection errors
        '''

        # Set API Key
        key_manager = self._recon.get_key_manager()
        key_manager.add_key("github_api", "my_invalid_key")

        # Set options
        options = self._module.get_options()
        self._recon.validate_options(self._module)
        self._module.preflight()

        # =====================================================================================
        # Test - Bad API Key
        # =====================================================================================
        self._module.run([self.TEST_REPO])
        self.assertInOutput(".*Invalid authentication key. Please check key and try again.*")

    def test_option_pagelimit(self):
        '''
        Tests the PAGELIMIT option
        '''

        # Tweak Options
        self._recon.set_verbosity(2)
        self._module.PAGE_SIZE = 1

        # =====================================================================================
        # Test - Default Page Limit
        # =====================================================================================
        options = self._module.get_options()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        self.assertInOutput(".*Fetching page: 1")
        self.assertNotInOutput(".*Fetching page: 2")

        # =====================================================================================
        # Test - Page Limit: 5
        # =====================================================================================
        options["pagelimit"] = 5
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        self.assertInOutput(".*Fetching page: 1")
        self.assertInOutput(".*Fetching page: 2")
        self.assertInOutput(".*Fetching page: 3")
        self.assertInOutput(".*Fetching page: 4")
        self.assertInOutput(".*Fetching page: 5")
        self.assertNotInOutput(".*Fetching page: 6")

        # =====================================================================================
        # Test: Page Limit Not valid Integer (String)
        # =====================================================================================
        options["pagelimit"] = "hello"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'PAGELIMIT' option => Not an integer", cm)

        # =====================================================================================
        # Test: Page Limit Not valid Integer (Float)
        # =====================================================================================
        options["pagelimit"] = 3.4
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'PAGELIMIT' option => Not an integer", cm)

    def test_option_dorks_file(self):
        '''
        Tests the DORKSFILE option
        '''
        self._recon.set_verbosity(2)

        # =====================================================================================
        # Test - File not set
        # =====================================================================================
        options = self._module.get_options()
        options["DORKSFILE"] = ""
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Value required for the 'DORKSFILE' option.", cm)

        # =====================================================================================
        # Test - File Doesn't Exist
        # =====================================================================================
        options = self._module.get_options()
        options["DORKSFILE"] = "/hello/123/thisisatest.txt"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual(
            "Validation failed for the 'DORKSFILE' option => The specified path does not point to a valid, "
            "existing file", cm
        )

        # =====================================================================================
        # Test - Check file is actually used
        # =====================================================================================
        self._create_tmp_dorks_file([
            "13832838", "fdssfsdgfgffd", "fsfsdfdsfsd"]
        )

        # Set options
        options["DORKSFILE"] = self.TMP_DORKS_FILE

        # Check initial Database state
        vulns = self.get_table_rows("vulnerabilities")
        self.assertEmpty(vulns)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        # Check Output
        self.assertInOutput(r".*Query \(1 of 3\).*")

        # =====================================================================================
        # Test - Empty keywords file
        # =====================================================================================
        self._create_tmp_dorks_file([])

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module.run([self.TEST_REPO])
        self.assertInOutput(".*Could not find any dorks in specified file.")

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def _create_tmp_dorks_file(self, dorks):
        '''
        Creates a temporary dorks file containing the specified dorks. Provides a way to override the list that
        we ship with

        :param dorks: The list of dorks to use
        :type dorks: list
        '''

        # Clear existing file
        if os.path.exists(self.TMP_DORKS_FILE):
            os.remove(self.TMP_DORKS_FILE)

        # Add entries
        with open(self.TMP_DORKS_FILE, "w") as tmp_dorks_file:
            for entry in dorks:
                tmp_dorks_file.write(f"{entry}\n")


