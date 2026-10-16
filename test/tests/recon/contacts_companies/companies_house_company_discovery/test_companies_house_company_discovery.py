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
# Companies House Company Discovery Module Test Case
# =====================================================================================
class TestCompaniesHouseCompanyDiscovery(ModuleTestCase):
    '''
    Tests the Companies House Company Discovery Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "recon/contacts-companies/companies_house_company_discovery"
    TEST_RESULTS_OFFICERS_FILENAME      = "test_results_officers.json"
    TEST_RESULTS_APPOINTMENTS_FILENAME  = "test_results_appointments.json"
    TEST_RESULTS_COMPANY_DATA_FILENAME  = "test_results_company_data.json"
    TEST_OFFICER                        = "John James Doe"

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
        self.test_results_officers = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_OFFICERS_FILENAME)
        self.test_results_appointments = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_APPOINTMENTS_FILENAME)
        self.test_results_company_data = os.path.join(os.path.dirname(__file__), self.TEST_RESULTS_COMPANY_DATA_FILENAME)

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
        companies = self.get_table_rows("companies")
        self.assertEmpty(companies)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_officers = self.test_results_officers
        self._module._test_results_file_officer_appointments = self.test_results_appointments
        self._module._test_results_file_company_data = self.test_results_company_data
        self._module.run([self.TEST_OFFICER])

        # Check Output
        self.assertInOutput(r".*Officers Processed:\t\t1")
        self.assertInOutput(r".*Appointments Processed:\t1")
        self.assertInOutput(r".*Companies Processed:\t1")

        # Check actual DB entries
        companies = self.get_table_rows("companies", True)
        self.assertLengthEqual(companies, 1)

        self.assertEqual(companies[0]["company"], "company_name redacted 01")

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
            self._module.run([self.TEST_OFFICER])
        self.assertExceptionStringEqual("Unexpected response from Companies House API: 404", cm)
        self._module.BASE_URL = URL

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        URL = self._module.BASE_URL
        self._module.BASE_URL = URL.replace(".uk", ".fds")
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_OFFICER])
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
        companies = self.get_table_rows("companies")
        self.assertEmpty(companies)

        options = self._module.get_options()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_officers = self.test_results_officers
        self._module._test_results_file_officer_appointments = self.test_results_appointments
        self._module._test_results_file_company_data = self.test_results_company_data

        self._module.run([self.TEST_OFFICER])

        self.assertInOutput(r".*Officers Processed:\t\t1")
        self.assertInOutput(r".*Appointments Processed:\t1")
        self.assertInOutput(r".*Companies Processed:\t1")
        self.assertInOutput(".*Performing exact match check:")
        companies = self.get_table_rows("companies")
        self.assertLengthEqual(companies, 1)

        # =====================================================================================
        # Test - False
        # =====================================================================================
        # Check initial Database state
        db = self.get_workspace_db()
        db.clear_table("companies")
        companies = self.get_table_rows("companies")
        self.assertEmpty(companies)

        options = self._module.get_options()
        options["EXACTMATCH"] = False
        self._console.clear_output()
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_officers = self.test_results_officers
        self._module._test_results_file_officer_appointments = self.test_results_appointments
        self._module._test_results_file_company_data = self.test_results_company_data

        self._module.run([self.TEST_OFFICER])

        self.assertInOutput(r".*Officers Processed:\t\t10")
        self.assertInOutput(r".*Appointments Processed:\t10")
        self.assertInOutput(r".*Companies Processed:\t1")
        self.assertNotInOutput(".*Performing exact match check:")
        companies = self.get_table_rows("companies")
        self.assertLengthEqual(companies, 1)

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
        companies = self.get_table_rows("companies")
        self.assertEmpty(companies)

        options = self._module.get_options()
        options["EXACTMATCH"] = False
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_officers = self.test_results_officers
        self._module._test_results_file_officer_appointments = self.test_results_appointments
        self._module._test_results_file_company_data = self.test_results_company_data

        self._module.run([self.TEST_OFFICER])

        self.assertInOutput(r".*Officers Processed:\t\t10")
        self.assertInOutput(r".*Appointments Processed:\t10")
        self.assertInOutput(r".*Companies Processed:\t1")
        self.assertNotInOutput(r".*Officer limit reached. Breaking")

        companies = self.get_table_rows("companies")
        self.assertLengthEqual(companies, 1)

        # =====================================================================================
        # Test - 5
        # =====================================================================================
        # Check initial Database state
        self._console.clear_output()
        db = self.get_workspace_db()
        db.clear_table("companies")
        companies = self.get_table_rows("companies")
        self.assertEmpty(companies)

        options["RESULTLIMIT"] = 5
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file_officers = self.test_results_officers
        self._module._test_results_file_officer_appointments = self.test_results_appointments
        self._module._test_results_file_company_data = self.test_results_company_data

        self._module.run([self.TEST_OFFICER])

        self.assertInOutput(r".*Officers Processed:\t\t5")
        self.assertInOutput(r".*Appointments Processed:\t5")
        self.assertInOutput(r".*Companies Processed:\t1")
        self.assertInOutput(r".*Officer limit reached. Breaking")
        companies = self.get_table_rows("companies")
        self.assertLengthEqual(companies, 1)

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
