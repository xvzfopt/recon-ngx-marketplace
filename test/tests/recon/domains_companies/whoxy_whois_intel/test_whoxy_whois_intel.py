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
# Whoxy Whois Intel Module Test Case Clas
# =====================================================================================
class TestWhoxyDomainIntel(ModuleTestCase):
    '''
    Tests the Whoxy Whois Intel Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY                   = 1
    FQN                         = "recon/domains-companies/whoxy_whois_intel"
    TEST_RESULTS_FILENAME       = "test_whoxy.json"
    TEST_RESULTS_FILE_ERROR     = "test_whoxy_whois_error.json"
    TEST_RESULTS_FILE_FULL      = "test_whoxy_whois_full.json"
    TEST_RESULTS_FILE_REDACTED  = "test_whoxy_whois_redacted.json"
    TEST_RESULTS_FILE_MIN       = "test_whoxy_whois_min.json"
    TEST_DOMAIN                 = "facebook.com"

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
        self.test_results_error_path = os.path.join(str(os.path.dirname(__file__)), self.TEST_RESULTS_FILE_ERROR)
        self.test_results_full_path = os.path.join(str(os.path.dirname(__file__)), self.TEST_RESULTS_FILE_FULL)
        self.test_results_min_path = os.path.join(str(os.path.dirname(__file__)), self.TEST_RESULTS_FILE_MIN)
        self.test_results_error_path = os.path.join(str(os.path.dirname(__file__)), self.TEST_RESULTS_FILE_ERROR)
        self.test_results_redacted_path = os.path.join(str(os.path.dirname(__file__)), self.TEST_RESULTS_FILE_REDACTED)

        # Wait to prevent annoying throttling
        time.sleep(1)

    # =====================================================================================
    # Unit tests
    # =====================================================================================
    def test_run_full_record(self):
        '''
        Tests execution of the Module when the Whois query returns a full record
        '''

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()
        options["confirm"] = "false"

        # Check Initial entries
        companies = self.get_table_rows("domains")
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(companies)
        self.assertEmpty(contacts)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_full_path
        self._module.run([self.TEST_DOMAIN])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Contacts created: 3")
        self.assertInOutput(r".*Companies created: 3")
        self.assertInOutput(r".*Credits Remaining")

        # Check Contacts
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(contacts, 3)

        # Check contact data
        self.assertEqual("Dave", contacts[0]["first_name"])
        self.assertEqual("Smith", contacts[0]["last_name"])
        self.assertEqual("London", contacts[0]["city"])
        self.assertEqual("England", contacts[0]["region"])
        self.assertEqual("United Kingdom", contacts[0]["country"])
        self.assertEqual("+78", contacts[0]["phone"])
        self.assertEqual("jsmith@fb.com", contacts[0]["email"])

        # Check companies
        companies = self.get_table_rows("companies", True)
        self.assertLengthEqual(contacts, 3)

        # Check company data
        self.assertEqual("Company 1", companies[0]["company"] )
        self.assertEqual("Company 2", companies[1]["company"] )
        self.assertEqual("Company 3", companies[2]["company"] )

    def test_run_redacted(self):
        '''
        Tests execution of the Module when the Whois query returns a record that is heavily redacted
        '''

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()
        options["confirm"] = "false"

        # Check Initial entries
        companies = self.get_table_rows("domains")
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(companies)
        self.assertEmpty(contacts)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_redacted_path
        self._module.run([self.TEST_DOMAIN])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Contacts created: 1")
        self.assertInOutput(r".*Companies created: 1")
        self.assertInOutput(r".*Credits Remaining")

        # Check Contacts
        contacts = self.get_table_rows("contacts", True)
        self.assertLengthEqual(contacts, 1)

        # Check contact data
        self.assertIsNone(contacts[0]["first_name"])
        self.assertIsNone(contacts[0]["last_name"])
        self.assertIsNone(contacts[0]["city"])
        self.assertIsNone(contacts[0]["phone"])
        self.assertEqual("Australia", contacts[0]["country"])
        self.assertEqual("New South Wales", contacts[0]["region"])
        self.assertEqual("7bd96a5bc65905fe8dd1f642d591b0b7-12873969@contact.gandi.net", contacts[0]["email"])

        # Check companies
        companies = self.get_table_rows("companies", True)
        self.assertLengthEqual(contacts, 1)

        # Check company data
        self.assertEqual("Canva Pty. Ltd.", companies[0]["company"] )

    def test_run_min_record(self):
        '''
        Tests execution of the Module when the Whois query returns a minimal record
        '''

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()
        options["confirm"] = "false"

        # Check Initial entries
        companies = self.get_table_rows("domains")
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(companies)
        self.assertEmpty(contacts)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_min_path
        self._module.run([self.TEST_DOMAIN])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Contacts created: 0")
        self.assertInOutput(r".*Companies created: 0")
        self.assertInOutput(r".*Credits Remaining")

        # Check Table Data
        contacts = self.get_table_rows("contacts", True)
        self.assertEmpty(contacts)
        companies = self.get_table_rows("companies", True)
        self.assertEmpty(companies)

    def test_run_error_record(self):
        '''
        Tests execution of the Module when the Whois query returns an error record
        '''

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()
        options["confirm"] = "false"

        # Check Initial entries
        companies = self.get_table_rows("domains")
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(companies)
        self.assertEmpty(contacts)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_error_path
        self._module.run([self.TEST_DOMAIN])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Contacts created: 0")
        self.assertInOutput(r".*Companies created: 0")
        self.assertInOutput(r".*Credits Remaining")

        # Check Table Data
        contacts = self.get_table_rows("contacts", True)
        self.assertEmpty(contacts)
        companies = self.get_table_rows("companies", True)
        self.assertEmpty(companies)

    def test_run_failures(self):
        '''
        Tests failure runs of the module
        '''

        # Set options
        self._recon.set_verbosity(2)
        options = self._module.get_options()
        options["confirm"] = "false"

        # Check Initial Database state
        companies = self.get_table_rows("domains")
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(companies)
        self.assertEmpty(contacts)

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()

        # Set Account balance
        # =====================================================================================
        # Test - No account credits
        # =====================================================================================
        self._module._account_balance = {"live_whois_balance": 0}
        # Execute Module
        self._module.run([self.TEST_DOMAIN])
        self.assertInOutput(".*No Whois Lookup credits on this account. Please add credits to use this module")

        # =====================================================================================
        # Test - Insufficient credits
        # =====================================================================================
        self._module._account_balance = {"live_whois_balance": 1}
        # Execute Module
        self._module.run([self.TEST_DOMAIN, self.TEST_DOMAIN])
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
            self._module.run([self.TEST_DOMAIN])
        self.assertExceptionStringEqual("Unexpected response from API. Please check debug output", cm)
        self._module.BASE_URL = URL

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        self._module.BASE_URL = self._module.BASE_URL.replace("com", "testgh23h")
        # Execute Module
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_DOMAIN])
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

        # =====================================================================================
        # Test - Unknown Domain Name - No errors thrown
        # =====================================================================================
        # Execute Module
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_DOMAIN])
        self.assertExceptionStringEqual("Whoxy API Error: Invalid API Key", cm)

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

    def test_filter_redaction(self):
        '''
        Tests that we can filter record values that have been redacted
        '''

        # Redacted
        self.assertIsNone(self._module.filter_redaction("REDACTED FOR PRIVACY"))
        self.assertIsNone(self._module.filter_redaction("redacted for privacy"))
        self.assertIsNone(self._module.filter_redaction("redacted."))
        self.assertIsNone(self._module.filter_redaction("privacy"))
        self.assertIsNone(self._module.filter_redaction("This information has been redacted"))

        # Not redacted
        self.assertEqual("hello", self._module.filter_redaction("hello"))
        self.assertEqual("admin@google.com", self._module.filter_redaction("admin@google.com"))
        self.assertEqual("private@hello.com", self._module.filter_redaction("private@hello.com"))
