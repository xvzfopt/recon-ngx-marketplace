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
# Whoxy Domain Discovery Module Test Case Clas
# =====================================================================================
class TestWhoxyDomainDiscovery(ModuleTestCase):
    '''
    Tests the Whoxy Domain Discovery Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY               = 1
    FQN                     = "recon/companies-domains/whoxy_domain_discovery"
    TEST_RESULTS_FILENAME   = "test_whoxy.json"
    TEST_COMPANY            = "Microsoft"

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

        # Check Initial entries
        domains = self.get_table_rows("domains")
        self.assertEmpty(domains)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_COMPANY])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Domain Names found: 100")

        self.assertInOutput(r".*Credits Remaining")

        # Check actual DB entries
        domains = self.get_table_rows("domains")
        self.assertLengthEqual(domains, 100)

    def test_run_failures(self):
        '''
        Tests failure runs of the module
        '''

        # Set options
        self._recon.set_verbosity(2)

        # Check Initial Database state
        domains = self.get_table_rows("domains")
        self.assertEmpty(domains)

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()

        # Set Account balance
        # =====================================================================================
        # Test - No account credits
        # =====================================================================================
        # self._module._account_balance = {"reverse_whois_balance": 0}
        # # Execute Module
        # self._module.run([self.TEST_COMPANY])
        # self.assertInOutput(".*No Reverse Whois Lookup credits on this account. Please add credits to use this module")

        # =====================================================================================
        # Test - Insufficient credits
        # =====================================================================================
        self._module._account_balance = {"reverse_whois_balance": 1}
        # Execute Module
        self._module.run([self.TEST_COMPANY, self.TEST_COMPANY])
        self.assertInOutput(
            r".*Query requires 2 credit\(s\), but there are only 1 available\. Please add more credits to continue.*"
        )

        # =====================================================================================
        # Test - Bad URL
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = self._module.BASE_URL.replace(".com", ".com/hello")
        # Execute Module
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY])
        self.assertExceptionStringEqual("Unexpected response from API. Please check debug output", cm)
        self._module.BASE_URL = URL

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        self._module.BASE_URL = self._module.BASE_URL.replace("com", "testgh23h")
        # Execute Module
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY])
        self.assertStartsWith(str(cm.exception), "Unable to reach Whoxy API: ")

    def test_invalid_api_key(self):
        '''
        Test Handling of connection errors
        '''

        # Set API Key
        key_manager = self._recon.get_key_manager()
        key_manager.add_key("whoxy_api", "my_invalid_key")

        # Set options
        options = self._module.get_options()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # =====================================================================================
        # Test - Unknown Domain Name - No errors thrown
        # =====================================================================================
        # Execute Module
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY])
        self.assertExceptionStringEqual("Whoxy API Error: Invalid API Key", cm)

    def test_option_pagelimit(self):
        '''
        Tests the PAGELIMIT option
        '''
        self._recon.set_verbosity(2)

        # =====================================================================================
        # Test - Default Page Limit
        # =====================================================================================
        options = self._module.get_options()
        options["confirm"] = "false"
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_COMPANY])

        self.assertInOutput(".*Fetching page: 1")
        self.assertNotInOutput(".*Fetching page: 2")

        # =====================================================================================
        # Test - Page Limit: 5
        # =====================================================================================
        options["pagelimit"] = 5
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
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
