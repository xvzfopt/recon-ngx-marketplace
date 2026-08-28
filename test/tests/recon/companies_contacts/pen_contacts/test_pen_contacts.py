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
# IANA PEN Contact Extractor Test Case Class
# =====================================================================================
class TestIANAPENContactExtractor(ModuleTestCase):
    '''
    Tests the IANA PEN Contact Extractor Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN                     = "recon/companies-contacts/pen_contacts"
    TEST_COMPANY_NAME       = "Microsoft"
    TEST_REGISTY_FILENAME   = "test_pen_registry.txt"

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
        self.test_results_path = os.path.join(os.path.dirname(__file__), self.TEST_REGISTY_FILENAME)
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
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(contacts)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_COMPANY_NAME])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Contacts created: 5")

        # =====================================================================================
        # Check DB Results
        # =====================================================================================
        contacts = self.get_table_rows("contacts")
        self.assertLengthEqual(contacts, 5)

        # Check Some entries
        self.assertEqual(contacts[0][0], "Paul")
        self.assertIsNone(contacts[0][1])
        self.assertEqual(contacts[0][2], "Russell")
        self.assertEqual(contacts[0][3], "paulr@microsoft.com")

        self.assertEqual(contacts[1][0], "Yves")
        self.assertEqual(contacts[1][1], "Frédéric")
        self.assertEqual(contacts[1][2], "N´Soussoula")
        self.assertEqual(contacts[1][3], "info@msuccug.de")

        self.assertEqual(contacts[2][0], "Ed")
        self.assertIsNone(contacts[2][1])
        self.assertEqual(contacts[2][2], "Price")
        self.assertEqual(contacts[2][3], "smallbasic@microsoft.com")
