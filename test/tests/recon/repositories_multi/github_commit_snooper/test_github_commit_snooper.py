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
# GitHub Commit Snooper Module Test Case Class
# =====================================================================================
class TestGitHubCommitSnooper(ModuleTestCase):
    '''
    Tests the GitHub Commit Snooper Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "recon/repositories-multi/github_commit_snooper"
    TEST_RESULTS_FILENAME   = "test_results.json"
    TEST_REPO               = ("lanmaster53", "recon-ng")

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
        profiles = self.get_table_rows("profiles")
        self.assertEmpty(contacts)
        self.assertEmpty(profiles)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Profiles discovered: 12")
        self.assertInOutput(r".*Contacts discovered: 14")

        # Check actual DB entries
        profiles = self.get_table_rows("profiles", True)
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(profiles, 12)
        self.assertLengthEqual(contacts, 14)

        self.assertEqual(contacts[0]["first_name"], "Tim")
        self.assertIsNone(contacts[0]["middle_name"])
        self.assertEqual(contacts[0]["last_name"], "Tomes")
        self.assertEqual(contacts[0]["email"], "tjt1980@gmail.com")
        self.assertEqual(contacts[0]["title"], "GitHub Contributor")

        self.assertEqual(contacts[4]["first_name"], "Dinkle")
        self.assertIsNone(contacts[4]["middle_name"])
        self.assertEqual(contacts[4]["last_name"], "Burger")
        self.assertEqual(contacts[4]["email"], "dinkelburgler@proton.me")
        self.assertEqual(contacts[4]["title"], "GitHub Contributor")

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
            self._module.run([self.TEST_REPO])
        self.assertExceptionStringEqual("Unexpected response from API: 404", cm)
        self._module.BASE_URL = URL

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = URL.replace(".com", ".fdsfsd")

        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_REPO])
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
        self._module.run([self.TEST_REPO])
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


    def test_option_extract_author(self):
        '''
        Tests the EXTRACTAUTHOR option
        '''


        # =====================================================================================
        # Test - Default Value (True)
        # =====================================================================================
        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()

        # Check initial Database state
        contacts = self.get_table_rows("contacts")
        profiles = self.get_table_rows("profiles")
        self.assertEmpty(contacts)
        self.assertEmpty(profiles)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Profiles discovered: 12")
        self.assertInOutput(r".*Contacts discovered: 14")

        # Check actual DB entries
        profiles = self.get_table_rows("profiles", True)
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(profiles, 12)
        self.assertLengthEqual(contacts, 14)

        self.assertEqual(contacts[0]["first_name"], "Tim")
        self.assertIsNone(contacts[0]["middle_name"])
        self.assertEqual(contacts[0]["last_name"], "Tomes")
        self.assertEqual(contacts[0]["email"], "tjt1980@gmail.com")
        self.assertEqual(contacts[0]["title"], "GitHub Contributor")

        # =====================================================================================
        # Test - False
        # =====================================================================================
        # Reset State
        db = self.get_workspace_db()
        db.clear_table("contacts")
        db.clear_table("profiles")
        contacts = self.get_table_rows("contacts")
        profiles = self.get_table_rows("profiles")
        self.assertEmpty(contacts)
        self.assertEmpty(profiles)
        self.clear_console_output()

        options["EXTRACTAUTHOR"] = False

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Profiles discovered: 2")
        self.assertInOutput(r".*Contacts discovered: 2")

        # Check actual DB entries
        profiles = self.get_table_rows("profiles", True)
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(profiles, 2)
        self.assertLengthEqual(contacts, 2)

        # =====================================================================================
        # Test - Invalid Values
        # =====================================================================================
        options["EXTRACTAUTHOR"] = 29
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'EXTRACTAUTHOR' option => Not a valid boolean value", cm)

        options["EXTRACTAUTHOR"] = "hello"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'EXTRACTAUTHOR' option => Not a valid boolean value", cm)

    def test_option_extract_committer(self):
        '''
        Tests the EXTRACTCOMMITTER option
        '''


        # =====================================================================================
        # Test - Default Value (True)
        # =====================================================================================
        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()

        # Check initial Database state
        contacts = self.get_table_rows("contacts")
        profiles = self.get_table_rows("profiles")
        self.assertEmpty(contacts)
        self.assertEmpty(profiles)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Profiles discovered: 12")
        self.assertInOutput(r".*Contacts discovered: 14")

        # Check actual DB entries
        profiles = self.get_table_rows("profiles", True)
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(profiles, 12)
        self.assertLengthEqual(contacts, 14)

        self.assertEqual(contacts[0]["first_name"], "Tim")
        self.assertIsNone(contacts[0]["middle_name"])
        self.assertEqual(contacts[0]["last_name"], "Tomes")
        self.assertEqual(contacts[0]["email"], "tjt1980@gmail.com")
        self.assertEqual(contacts[0]["title"], "GitHub Contributor")

        # =====================================================================================
        # Test - False
        # =====================================================================================
        # Reset State
        db = self.get_workspace_db()
        db.clear_table("contacts")
        db.clear_table("profiles")
        contacts = self.get_table_rows("contacts")
        profiles = self.get_table_rows("profiles")
        self.assertEmpty(contacts)
        self.assertEmpty(profiles)
        self.clear_console_output()

        options["EXTRACTCOMMITTER"] = False

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_REPO])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Profiles discovered: 11")
        self.assertInOutput(r".*Contacts discovered: 13")

        # Check actual DB entries
        profiles = self.get_table_rows("profiles", True)
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(profiles, 11)
        self.assertLengthEqual(contacts, 13)

        # =====================================================================================
        # Test - Invalid Values
        # =====================================================================================
        options["EXTRACTCOMMITTER"] = 29
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'EXTRACTCOMMITTER' option => Not a valid boolean value", cm)

        options["EXTRACTCOMMITTER"] = "hello"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'EXTRACTCOMMITTER' option => Not a valid boolean value", cm)

