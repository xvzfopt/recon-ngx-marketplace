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
# IANA PEN Domain Names Extractor Test Case Class
# =====================================================================================
class TestIANAPENDomainNamesExtractor(ModuleTestCase):
    '''
    Tests the IANA PEN Domain Names Extractor Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN                     = "recon/companies-domains/pen_domains"
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
        domains = self.get_table_rows("domains")
        self.assertEmpty(domains)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module._test_results_file = self.test_results_path
        self._module.run([self.TEST_COMPANY_NAME])

        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Domain Names found: 2")

        # =====================================================================================
        # Check DB Results
        # =====================================================================================
        domains = self.get_table_rows("domains")
        self.assertLengthEqual(domains, 2)

        # Check Some entries
        self.assertEqual(domains[0][0], "microsoft.com")
        self.assertEqual(domains[1][0], "msuccug.de")
