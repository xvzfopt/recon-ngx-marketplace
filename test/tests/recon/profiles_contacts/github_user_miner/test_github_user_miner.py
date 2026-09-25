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
class TestGitHubUserMiner(ModuleTestCase):
    '''
    Tests the GitHub User Miner Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "recon/profiles-contacts/github_user_miner"
    TEST_RESULTS_FILENAME   = "test_results_user.json"
    TEST_USER               = "jdoe123"

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
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(contacts)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_USER])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Contacts created: 1")

        # Check actual DB entries
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(contacts, 1)

        self.assertEqual(contacts[0]["first_name"], "John")
        self.assertEqual(contacts[0]["middle_name"], "Peter")
        self.assertEqual(contacts[0]["last_name"], "Doe")
        self.assertEqual(contacts[0]["region"], "Stuttgart, Germany")
        self.assertEqual(contacts[0]["email"], "john.doe@microsoft.com")
        self.assertEqual(contacts[0]["title"], "GitHub Contributor at Microsoft")
        self.assertEqual(contacts[0]["notes"], "Bio: This is my bio, how great am I?!")

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
            self._module.run([self.TEST_USER])
        self.assertExceptionStringEqual("Unexpected response from API: 404", cm)
        self._module.BASE_URL = URL

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = URL.replace(".com", ".fdsfsd")

        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_USER])
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
        self._module.run([self.TEST_USER])
        self.assertInOutput(".*Invalid authentication key. Please check key and try again.*")