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
# ViewDNS Domain Names Finder Test Case Class
# =====================================================================================
class TestViewDNSDomainNamesFinder(ModuleTestCase):
    '''
    Tests the ViewDNS Domain Names Finder Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN                 = "recon/companies-domains/viewdns_domains_finder"
    TEST_COMPANY_NAME   = "Splunk"
    TEST_RESPONSE_FILE  = "test_results.json"

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
        self.test_results_path = os.path.join(os.path.dirname(__file__), self.TEST_RESPONSE_FILE)
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

        # Check Initial Database state
        domains = self.get_table_rows("domains")
        self.assertEmpty(domains)

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # Set account balance
        self._module._account_balance = {
            "trial": {
                "limit": "250",
                "usage": "8"
            },
            "prepaid": {
                "balance": "1000"
            }
        }

        # Execute Module
        self._module.run([self.TEST_COMPANY_NAME])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Domain Names found: 5")

        # =====================================================================================
        # Check DB Results
        # =====================================================================================
        domains = self.get_table_rows("domains")
        self.assertLengthEqual(domains, 5)

        # Check Some entries
        self.assertEqual(domains[0][0], "demo1.com")
        self.assertEqual(domains[1][0], "demo2.com")
        self.assertEqual(domains[2][0], "demo3.com")
        self.assertEqual(domains[3][0], "demo4.com")
        self.assertEqual(domains[4][0], "demo5.com")

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
        self._module._account_balance = {
            "monthly": {
                "limit": "250",
                "usage": "200"
            },
            "prepaid": {
                "balance": "1000"
            }
        }

        # =====================================================================================
        # Test - Bad URL
        # =====================================================================================
        EP_REVERSEWHOIS = self._module.EP_REVERSEWHOIS
        self._module.EP_REVERSEWHOIS = "test/blah"
        # Execute Module
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY_NAME])
        self.assertExceptionStringEqual("Unexpected response from API: 404", cm)
        self._module.EP_REVERSEWHOIS = EP_REVERSEWHOIS

        # =====================================================================================
        # Test - Bad Host
        # =====================================================================================
        self._module.BASE_URL = self._module.BASE_URL.replace("info", "testgh23h")
        # Execute Module
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY_NAME])
        self.assertStartsWith(str(cm.exception), "Unable to reach ViewDNS API: ")

    def test_bad_api_key(self):
        '''
        Tests handling when a bad API key is specified
        '''

        # Set options
        self._recon.set_verbosity(2)

        # Set API Key
        key_manager = self._recon.get_key_manager()
        key_manager.add_key("viewdns_api", "my_invalid_key")

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.run([self.TEST_COMPANY_NAME])
        self.assertExceptionStringEqual("API Error: Invalid API Key Provided.", cm)

    def test_validate_account_balance(self):
        '''
        Tests validation of an account's balance to ensure that there are enough credits to perform a specified
        number of queries
        '''

        # Set options
        self._recon.set_verbosity(2)

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # =====================================================================================
        # TEST - Sufficient Monthly credits
        # =====================================================================================
        self._module._account_balance = {
            "monthly": {
                "limit": "250",
                "usage": "200"
            },
            "prepaid": {
                "balance": "0"
            }
        }
        self._module.validate_account_balance(5)

        # =====================================================================================
        # TEST - Sufficient Prepaid credits
        # =====================================================================================
        self._module._account_balance = {
            "monthly": {
                "limit": "250",
                "usage": "200"
            },
            "prepaid": {
                "balance": "1000"
            }
        }
        self._module.validate_account_balance(1000)

        # =====================================================================================
        # TEST - Insufficient Prepaid or Monthly credits
        # =====================================================================================
        self._module._account_balance = {
            "monthly": {
                "limit": "250",
                "usage": "200"
            },
            "prepaid": {
                "balance": "1000"
            }
        }
        with self.assertRaises(ModuleValidationException) as cm:
            self._module.validate_account_balance(10000)
        self.assertExceptionStringEqual(
            "Insufficient balance. Please adjust your paid plan, try again later, or purchase prepaid credits",
            cm
        )

        # =====================================================================================
        # TEST - Trial account - Can't run queries
        # =====================================================================================
        self._module._account_balance = {
            "trial": {
                "limit": "250",
                "usage": "8"
            },
            "prepaid": {
                "balance": "0"
            }
        }
        with self.assertRaises(ModuleValidationException) as cm:
            self._module.validate_account_balance()
        self.assertExceptionStringEqual(
            "This module does not support ViewDNS trial accounts. Please upgrade to a paid plan and try again",
            cm
        )

    def test_is_trial_account(self):
        '''
        Tests that we can check if an account is a trial account
        '''

        # Set options
        self._recon.set_verbosity(2)

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # =====================================================================================
        # TEST - Trial account
        # =====================================================================================
        self._module._account_balance = {
            "trial": {
                "limit": "250",
                "usage": "8"
            },
            "prepaid": {
                "balance": "1000"
            }
        }
        self.assertTrue(self._module.is_trial_account())

        # =====================================================================================
        # TEST - Not a Trial account
        # =====================================================================================
        self._module._account_balance = {
            "monthly": {
                "limit": "250",
                "usage": "8"
            },
            "prepaid": {
                "balance": "1000"
            }
        }
        self.assertFalse(self._module.is_trial_account())

    def test_get_prepaid_remaining_credits(self):
        '''
        Tests we can get an account's prepaid remaining credits
        '''

        # Set options
        self._recon.set_verbosity(2)

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # =====================================================================================
        # TEST - 1000 Prepaid credits remaining
        # =====================================================================================
        self._module._account_balance = {
            "trial": {
                "limit": "250",
                "usage": "8"
            },
            "prepaid": {
                "balance": "1000"
            }
        }
        self.assertEqual(1000, self._module.get_prepaid_remaining_credits())

        # =====================================================================================
        # TEST - 0 Prepaid credits remaining
        # =====================================================================================
        self._module._account_balance = {
            "trial": {
                "limit": "250",
                "usage": "8"
            },
            "prepaid": {
                "balance": "0"
            }
        }
        self.assertEqual(0, self._module.get_prepaid_remaining_credits())

        # =====================================================================================
        # TEST - Negative balance
        # =====================================================================================
        self._module._account_balance = {
            "trial": {
                "limit": "250",
                "usage": "8"
            },
            "prepaid": {
                "balance": "-500"
            }
        }
        self.assertEqual(0, self._module.get_prepaid_remaining_credits())

    def test_get_monthly_remaining_credits(self):
        '''
        Tests we can get an account's monthly remaining credits
        '''

        # Set options
        self._recon.set_verbosity(2)

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # =====================================================================================
        # TEST - No monthly subscription
        # =====================================================================================
        self._module._account_balance = {
            "trial": {
                "limit": "250",
                "usage": "8"
            },
            "prepaid": {
                "balance": "1000"
            }
        }
        self.assertEqual(0, self._module.get_monthly_remaining_credits())

        # =====================================================================================
        # TEST - 1000 monthly credits remaining
        # =====================================================================================
        self._module._account_balance = {
            "monthly": {
                "limit": "10000",
                "usage": "9000"
            },
            "prepaid": {
                "balance": "0"
            }
        }
        self.assertEqual(1000, self._module.get_monthly_remaining_credits())

        # =====================================================================================
        # TEST - Monthly limit reached
        # =====================================================================================
        self._module._account_balance = {
            "monthly": {
                "limit": "10000",
                "usage": "10000"
            },
            "prepaid": {
                "balance": "0"
            }
        }
        self.assertEqual(0, self._module.get_monthly_remaining_credits())

        # =====================================================================================
        # TEST - Monthly limit exceeded
        # =====================================================================================
        self._module._account_balance = {
            "monthly": {
                "limit": "10000",
                "usage": "11000"
            },
            "prepaid": {
                "balance": "0"
            }
        }
        self.assertEqual(0, self._module.get_monthly_remaining_credits())


    def test_fetch_account_balance_error(self):
        '''
        Tests error/exception handling in the fetch_account_balance function
        '''

        # Set options
        self._recon.set_verbosity(2)

        # Set up Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path

        # Set API Key
        key_manager = self._recon.get_key_manager()
        self._module._api_key = key_manager.get_key_value("viewdns_api")

        # =====================================================================================
        # Test - Bad URL
        # =====================================================================================
        EP_ACCOUNT = self._module.EP_ACCOUNT
        self._module.EP_ACCOUNT = "test/blah"

        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.fetch_account_balance()
        self.assertExceptionStringEqual("Unexpected response from API: 404", cm)
        self._module.EP_ACCOUNT = EP_ACCOUNT

        # =====================================================================================
        # Test - Bad host
        # =====================================================================================
        self._module.BASE_URL = self._module.BASE_URL.replace("info", "test12gh")
        with self.assertRaises(ModuleRuntimeException) as cm:
            self._module.fetch_account_balance()
        self.assertStartsWith(str(cm.exception), "Unable to reach ViewDNS API: ")
