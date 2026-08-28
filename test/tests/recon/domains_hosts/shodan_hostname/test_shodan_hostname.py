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
class TestShodanHostname(ModuleTestCase):
    '''
    Tests the Shodan Hostname Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "recon/domains-hosts/shodan_hostname"
    TEST_RESULTS_FILENAME = "test_results.json"

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
        self.test_results_path = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_FILENAME)
        self._module._test_results_file = self.test_results_path

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
        options["confirm"] = "false"

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run(["vultrusercontent.com"])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Hosts discovered: 100")
        self.assertInOutput(r".*Ports discovered: 126")

        self.assertInOutput(r".*Query Credits Remaining")
        self.assertInOutput(r".*Scan Credits Remaining")

        results = self.get_workspace_db().query("select * from ports")

    def test_invalid_api_key(self):
        '''
        Test Handling of connection errors
        '''

        # Set options
        options = self._module.get_options()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # Set API Key
        key_manager = self._recon.get_key_manager()
        key_manager.add_key("shodan_api", "my_invalid_key")

        # =====================================================================================
        # Test - Unknown Domain Name - No errors thrown
        # =====================================================================================
        # Execute Module
        self._module.run(["fdsfdsfsdfdsjjjdsjfs883838d.com"])

        # =====================================================================================
        # Test - Bad API Key
        # =====================================================================================
        self._module.run(["vultrusercontent.com"])
        self.assertInOutput(".*The configured Shodan API Key is invalid.*")

    def test_option_pagelimit(self):
        '''
        Tests the PAGELIMIT option
        '''
        self._recon.set_verbosity(2)

        # =====================================================================================
        # Test - Default Page Limit
        # =====================================================================================
        options = self._module.get_options()
        options["confirm"] = False
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run(["vultrusercontent.com"])

        self.assertInOutput(".*Fetching page: 1")
        self.assertNotInOutput(".*Fetching page: 2")

        # =====================================================================================
        # Test - Page Limit: 5
        # =====================================================================================
        options["pagelimit"] = 5
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run(["vultrusercontent.com"])

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


    def test_option_confirm(self):
        '''
        Tests the CONFIRM option.

        Note: We can't test this (currently) to the full extent, as it requires user interaction
        '''
        self._recon.set_verbosity(1)

        # =====================================================================================
        # Test - Confirm not valid 1
        # =====================================================================================
        options = self._module.get_options()
        options["confirm"] = "Hello"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'CONFIRM' option => Not a valid boolean value", cm)

        # =====================================================================================
        # Test - Confirm not valid 2
        # =====================================================================================
        options = self._module.get_options()
        options["confirm"] = 99
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'CONFIRM' option => Not a valid boolean value", cm)

        # =====================================================================================
        # Test - Confirm not valid 2
        # =====================================================================================
        options = self._module.get_options()
        options["confirm"] = 0
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'CONFIRM' option => Not a valid boolean value", cm)
