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
# Companies House Contact Discovery Module Test Case
# =====================================================================================
class TestCompaniesHouseContactDiscovery(ModuleTestCase):
    '''
    Tests the Companies House Contact Discovery Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "recon/companies-contacts/companies_house_contact_discovery"
    TEST_RESULTS_COMPANIES_FILENAME     = "test_results_companies.json"
    TEST_RESULTS_OFFICERS_FILENAME      = "test_results_officers.json"
    TEST_COMPANY                        = "one drive holdings limited"

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
        self.test_results_companies = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_COMPANIES_FILENAME)
        self.test_results_officers = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_OFFICERS_FILENAME)

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

        # Check initial Database state
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(contacts)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_companies = self.test_results_companies
        self._module._test_results_file_officers = self.test_results_officers
        self._module.run([self.TEST_COMPANY])

        # Check Output
        self.assertInOutput(r".*Company \(1 of 1\).*")
        self.assertInOutput(r".*Contacts Created:\t6")
        self.assertInOutput(r".*Contacts Skipped:\t1")

        # Check actual DB entries
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(contacts, 6)

        self.assertEqual(contacts[0]["city"], "New York")
        self.assertEqual(contacts[0]["country"], "United States")
        self.assertEqual(contacts[0]["region"], "New York")
        self.assertEqual(contacts[0]["title"], "director")
        self.assertEqual(contacts[0]["first_name"], "Paul")
        self.assertEqual(contacts[0]["middle_name"], "Jonathan")
        self.assertEqual(contacts[0]["last_name"], "Campbell-di cieri")

        self.assertEqual(contacts[5]["city"], "San Miniato")
        self.assertEqual(contacts[5]["country"], "Italy")
        self.assertEqual(contacts[5]["region"], "Pisa")
        self.assertEqual(contacts[5]["title"], "director")
        self.assertEqual(contacts[5]["first_name"], "Brett")
        self.assertEqual(contacts[5]["middle_name"], "James")
        self.assertEqual(contacts[5]["last_name"], "Whiteley")

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
        self._module.BASE_URL = URL.replace(".uk", ".uk/test123")
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY])
        self.assertExceptionStringEqual("Unexpected response from Companies House API: 404", cm)
        self._module.BASE_URL = URL

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = URL.replace(".uk", ".fds")
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY])
        self.assertStartsWith(str(cm.exception), "Unable to reach Companies House API: ")
        self._module.BASE_URL = URL

    def test_option_exactmatch(self):
        '''
        Tests the EXACTMATCH option
        '''
        self._recon.set_verbosity(2)

        # =====================================================================================
        # Test - Default (True)
        # =====================================================================================
        # Check initial Database state
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(contacts)

        options = self._module.get_options()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_companies = self.test_results_companies
        self._module._test_results_file_officers = self.test_results_officers

        self._module.run([self.TEST_COMPANY])

        self.assertInOutput(".*Contacts Created:\t6")
        self.assertInOutput(".*Contacts Skipped:\t1")
        self.assertInOutput(".*Performing exact match check:")
        contacts = self.get_table_rows("contacts")
        self.assertLengthEqual(contacts, 6)

        # =====================================================================================
        # Test - False
        # =====================================================================================
        # Check initial Database state
        db = self.get_workspace_db()
        db.clear_table("contacts")
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(contacts)

        options = self._module.get_options()
        options["EXACTMATCH"] = False
        self._console.clear_output()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_companies = self.test_results_companies
        self._module._test_results_file_officers = self.test_results_officers

        self._module.run([self.TEST_COMPANY])

        self.assertInOutput(".*Contacts Created:\t6")
        self.assertInOutput(".*Contacts Skipped:\t64")
        self.assertNotInOutput(".*Performing exact match check:")
        contacts = self.get_table_rows("contacts")
        self.assertLengthEqual(contacts, 6)

        # =====================================================================================
        # Test: Option Not valid Boolean (String)
        # =====================================================================================
        options["EXACTMATCH"] = "hello"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'EXACTMATCH' option => Not a valid boolean value", cm)

        # =====================================================================================
        # Test: Option Not valid Boolean (Integer)
        # =====================================================================================
        options["EXACTMATCH"] = 3
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'EXACTMATCH' option => Not a valid boolean value", cm)

    def test_option_result_limit(self):
        '''
        Tests the RESULTLIMIT option
        '''
        self._recon.set_verbosity(2)

        # =====================================================================================
        # Test - Default (10)
        # =====================================================================================
        # Check initial Database state
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(contacts)

        options = self._module.get_options()
        options["EXACTMATCH"] = False
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_companies = self.test_results_companies
        self._module._test_results_file_officers = self.test_results_officers

        self._module.run([self.TEST_COMPANY])

        self.assertInOutput(r".*Company \(1 of 10\).*")
        self.assertInOutput(".*Contacts Created:\t6")
        self.assertInOutput(".*Contacts Skipped:\t64")
        contacts = self.get_table_rows("contacts")
        self.assertLengthEqual(contacts, 6)

        # =====================================================================================
        # Test - 5
        # =====================================================================================
        # Check initial Database state
        self._console.clear_output()
        db = self.get_workspace_db()
        db.clear_table("contacts")
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(contacts)

        options["RESULTLIMIT"] = 5
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_companies = self.test_results_companies
        self._module._test_results_file_officers = self.test_results_officers

        self._module.run([self.TEST_COMPANY])

        self.assertInOutput(r".*Company \(1 of 5\).*")
        self.assertInOutput(".*Contacts Created:\t6")
        self.assertInOutput(".*Contacts Skipped:\t29")
        contacts = self.get_table_rows("contacts")
        self.assertLengthEqual(contacts, 6)

        # =====================================================================================
        # Test: Option Not valid Integer (String)
        # =====================================================================================
        options["RESULTLIMIT"] = "hello"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'RESULTLIMIT' option => Not an integer", cm)

        # =====================================================================================
        # Test: Option Not valid Integer (float)
        # =====================================================================================
        options["RESULTLIMIT"] = 3.4
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module)
        self.assertExceptionStringEqual("Validation failed for the 'RESULTLIMIT' option => Not an integer", cm)
