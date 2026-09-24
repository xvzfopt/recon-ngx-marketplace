# =====================================================================================
# Imports: External
# =====================================================================================
import os
import time

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.sdk.exceptions import *
from module_test_case import ModuleTestCase

# =====================================================================================
# Base Test Case Class
# =====================================================================================
class TestGitHubCompanyMiner(ModuleTestCase):
    '''
    Tests the GitHub Company Miner Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "recon/companies-multi/github_company_miner"
    TEST_RESULTS_FILENAME_MEMBERS   = "test_results_members.json"
    TEST_RESULTS_FILENAME_REPOS     = "test_results_repos.json"
    TEST_COMPANY                    = "Microsoft"

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

        # Misc Props
        self.test_results_path_members = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_FILENAME_MEMBERS)
        self.test_results_path_repos = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_FILENAME_REPOS)

        # Wait to prevent annoying throttling
        time.sleep(1)

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
        profiles = self.get_table_rows("profiles")
        repos = self.get_table_rows("repositories")
        self.assertEmpty(profiles)
        self.assertEmpty(repos)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_members = self.test_results_path_members
        self._module._test_results_file_repos = self.test_results_path_repos
        self._module.run([self.TEST_COMPANY])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Repositories discovered: 27")
        self.assertInOutput(r".*Profiles discovered: 30")
        self.assertInOutput(r".*Companies processed: 1")

        # Check actual DB entries
        profiles = self.get_table_rows("profiles")
        repos = self.get_table_rows("repositories")
        self.assertLengthEqual(profiles, 30)
        self.assertLengthEqual(repos, 30)

    def test_run_failures(self):
        '''
        Tests failure runs of the module
        '''

        # Set options
        self._recon.set_verbosity(1)

        # Set Up Module
        self._recon.validate_options(self._module)
        self._module.preflight()

        # =====================================================================================
        # Test - Bad URL
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = URL.replace(".com", ".com/blah")

        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY])
        self.assertExceptionStringEqual("Unexpected response from API: 404", cm)
        self._module.BASE_URL = URL

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = URL.replace(".com", ".fdsfsd")

        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY])
        self.assertStartsWith(str(cm.exception), "Unable to reach GitHub API: ")
        self._module.BASE_URL = URL

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
        self._module.run([self.TEST_COMPANY])
        self.assertInOutput(".*Invalid authentication key. Please check key and try again.*")

    def test_option_pagelimit(self):
        '''
        Tests the PAGELIMIT option
        '''
        self._recon.set_verbosity(2)

        # =====================================================================================
        # Test - Default Page Limit
        # =====================================================================================
        options = self._module.get_options()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_members = self.test_results_path_members
        self._module._test_results_file_repos = self.test_results_path_repos
        self._module.run([self.TEST_COMPANY])

        self.assertInOutput(".*Fetching page: 1")
        self.assertNotInOutput(".*Fetching page: 2")

        # =====================================================================================
        # Test - Page Limit: 5
        # =====================================================================================
        options["pagelimit"] = 5
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_members = self.test_results_path_members
        self._module._test_results_file_repos = self.test_results_path_repos
        self._module.run([self.TEST_COMPANY])

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

    def test_option_ignore_forks(self):
        '''
        Tests the IGNOREFORKS option.

        '''
        self._recon.set_verbosity(2)

        # =====================================================================================
        # Test - Default (True)
        # =====================================================================================
        options = self._module.get_options()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_members = self.test_results_path_members
        self._module._test_results_file_repos = self.test_results_path_repos
        self._module.run([self.TEST_COMPANY])

        # Check Output
        self.assertInOutput(".*Ignoring fork")

        # =====================================================================================
        # Test - False
        # =====================================================================================
        self.clear_console_output()
        options = self._module.get_options()
        options["ignoreforks"] = False
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_members = self.test_results_path_members
        self._module._test_results_file_repos = self.test_results_path_repos
        self._module.run([self.TEST_COMPANY])

        # Check Output
        self.assertNotInOutput(".*Ignoring fork")

        # =====================================================================================
        # Test - Bad Option value
        # =====================================================================================
        options["ignoreforks"] = "hello"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'IGNOREFORKS' option => Not a valid boolean value", cm)
