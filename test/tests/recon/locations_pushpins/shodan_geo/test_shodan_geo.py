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
class TestShodanGeoLocationSearch(ModuleTestCase):
    '''
    Tests the Shodan Geolocation Search Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "recon/locations-pushpins/shodan_geo"
    TEST_RESULTS_FILENAME = "test_results.json"
    TEST_LOCATION = "48.91667,2.38333"

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

        # Check Initial State
        db = self.get_workspace_db()
        db.clear_table("pushpins")
        results = db.query("SELECT * FROM pushpins")
        self.assertEmpty(results)

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()
        options["confirm"] = "false"

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_LOCATION])

        self.assertInOutput(r".*Location \(1 of 1\): %s" % self.TEST_LOCATION)
        self.assertInOutput(r".*Pushpins identified: 346")

        self.assertInOutput(r".*Query Credits Remaining")
        self.assertInOutput(r".*Scan Credits Remaining")

        # Check Pushpin entries were created
        pushpin_entries = db.query("SELECT * FROM pushpins")
        self.assertLengthEqual(pushpin_entries, 346)

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
        # Test - Bad API Key
        # =====================================================================================
        self._module.run([self.TEST_LOCATION])
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
        self._module.run([self.TEST_LOCATION])

        self.assertInOutput(".*Fetching page: 1")
        self.assertNotInOutput(".*Fetching page: 2")

        # =====================================================================================
        # Test - Page Limit: 5
        # =====================================================================================
        options["pagelimit"] = 5
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_LOCATION])

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

    def test_option_radius(self):
        '''
        Tests the RADIUS option
        '''
        self._recon.set_verbosity(1)
        options = self._module.get_options()
        options["confirm"] = False

        # =====================================================================================
        # Test - Default Radius
        # =====================================================================================
        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_LOCATION])

        self.assertInOutput(r".*Search Radius: 1 KM")

        # =====================================================================================
        # Test - 5 KM Radius
        # =====================================================================================
        # Execute Module
        options["radius"] = 15
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_LOCATION])

        self.assertInOutput(r".*Search Radius: 15 KM")

        # =====================================================================================
        # Test - Radius not valid
        # =====================================================================================
        options = self._module.get_options()
        options["radius"] = "Hello"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'RADIUS' option => Not an integer", cm)
