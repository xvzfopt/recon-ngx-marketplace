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
# SerpApi LinkedIn Harvester Test Case Class
# =====================================================================================
class TestSerpApiLinkedInHarvester(ModuleTestCase):
    '''
    Tests the SerpApi LinkedIn Harvester Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN                                 = "recon/companies-multi/serpapi_linkedin_harvester"
    TEST_COMPANY_NAME                   = "Microsoft"
    TEST_RESULTS_FILENAME_BAIDU         = "test_results_serp_baidu.json"
    TEST_RESULTS_FILENAME_DUCKDUCKGO    = "test_results_serp_duckduckgo.json"
    TEST_RESULTS_FILENAME_GOOGLE        = "test_results_serp_google.json"
    TEST_RESULTS_FILENAME_YAHOO         = "test_results_serp_yahoo.json"
    TEST_RESULTS_FILENAME_YANDEX        = "test_results_serp_yandex.json"

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
        self.test_results_path = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_FILENAME_GOOGLE)
        self._module._test_results_file = self.test_results_path

    # =====================================================================================
    # Unit tests
    # =====================================================================================
    def test_successful_run(self):
        '''
        Tests successful execution of the Module
        '''

        # Set options
        self._recon.set_verbosity(2)
        options = self._module.get_options()
        options["confirm"] = "false"

        # Check Initial Database state
        db = self.get_workspace_db()
        self.assertEmpty(db.query("SELECT * FROM profiles"))
        self.assertEmpty(db.query("SELECT * FROM contacts"))

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_COMPANY_NAME])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Contacts created: 10")
        self.assertInOutput(r".*Profiles created: 10")

        self.assertInOutput(r".*Processed page: 1")
        self.assertInOutput(r".*Page Limit reached: 1")

        self.assertInOutput(r".*SERPAPI STATUS")
        self.assertInOutput(r".*Total Searches Remaining")
        self.assertInOutput(r".*Hourly Searches Remaining")

        # =====================================================================================
        # Check DB Results
        # =====================================================================================
        contacts = db.query("SELECT * FROM contacts")
        profiles = db.query("SELECT * FROM profiles")
        self.assertLengthEqual(contacts, 10)
        self.assertLengthEqual(profiles, 10)

        # Check Some entries
        self.assertEqual("Omar", contacts[0][0])            # First Name
        self.assertIsNone(contacts[0][1])                       # Middle Name
        self.assertEqual("Shahine", contacts[0][2])         # Last Name
        self.assertEqual("Undetermined", contacts[0][4])    # Job Title

        self.assertEqual("Keith", contacts[9][0])           # First Name
        self.assertIsNone(contacts[9][1])                        # Middle Name
        self.assertEqual("Boyd", contacts[9][2])            # Last Name
        self.assertEqual("Senior Director", contacts[9][4]) # Job Title

    def test_invalid_api_key(self):
        '''
        Test Handling of connection errors
        '''

        # Set options
        options = self._module.get_options()
        options["confirm"] = False
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # Set API Key
        key_manager = self._recon.get_key_manager()
        key_manager.add_key("serpapi_api", "my_invalid_key")

        self._module.run([self.TEST_COMPANY_NAME])
        self.assertInOutput(".*The configured SerpApi API key is invalid.*")

    def test_option_engine(self):
        '''
        Tests the ENGINE option
        '''
        self._recon.set_verbosity(2)
        options = self._module.get_options()
        options["confirm"] = False

        # =====================================================================================
        # Test - Default Engine
        # =====================================================================================
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_COMPANY_NAME])

        self.assertInOutput(f".*Selected Engine: {self._module.meta.options[1].default}")
        self.assertInOutput(".*Processed page: 1")
        self.assertInOutput(".*Page Limit reached: 1")

        # =====================================================================================
        # Test - Custom Engine - Bing
        # =====================================================================================
        options["engine"] = "bing"
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_COMPANY_NAME])

        self.assertInOutput(f".*Selected Engine: bing")
        self.assertInOutput(".*Processed page: 1")
        self.assertInOutput(".*Page Limit reached: 1")

        # =====================================================================================
        # Test - Unknown Engine
        # =====================================================================================
        options["engine"] = "hello!"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual(
            "Validation failed for the 'ENGINE' option => The supplied value is not within the list of supported"
            " choices: google, bing, duckduckgo, yahoo, yandex, baidu",
            cm
        )

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
        self._module.run([self.TEST_COMPANY_NAME])

        self.assertInOutput(".*Processed page: 1")
        self.assertInOutput(".*Page Limit reached: 1")

        # =====================================================================================
        # Test - Page Limit: 5
        # =====================================================================================
        options["pagelimit"] = 5
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_COMPANY_NAME])

        self.assertInOutput(".*Processed page: 1")
        self.assertInOutput(".*Processed page: 2")
        self.assertInOutput(".*Processed page: 3")
        self.assertInOutput(".*Processed page: 4")
        self.assertInOutput(".*Processed page: 5")
        self.assertInOutput(".*Page Limit reached: 5")
        self.assertNotInOutput(".*Processed page: 6")

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
