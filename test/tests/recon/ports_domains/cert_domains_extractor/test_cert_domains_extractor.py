# =====================================================================================
# Imports: External
# =====================================================================================
import os

# =====================================================================================
# Imports: Internal
# =====================================================================================
from module_test_case import ModuleTestCase

# =====================================================================================
# Certificate Domain Names Extractor Test Case Class
# =====================================================================================
class TestCertDomainsExtractor(ModuleTestCase):
    '''
    Tests the Cert Domain Names Extractor Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY       = 1
    FQN             = "recon/ports-domains/cert_domains_extractor"
    TEST_TARGET     = ("127.0.0.1", "6767",)
    TEST_ROOT_PATH  = os.path.dirname(__file__)
    PATH_CERT       = os.path.join(TEST_ROOT_PATH, "cert.pem")
    PATH_KEY        = os.path.join(TEST_ROOT_PATH, "key.pem")

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

        # Start HTTP test server
        self.setUpHTTPServer(certfile=self.PATH_CERT, keyfile=self.PATH_KEY)

    # =====================================================================================
    # Unit tests
    # =====================================================================================
    def test_successful_run(self):
        '''
        Tests successful execution of the Module

        :Note: Due to the way in which we're connecting to the HTTP server, it will throw a Broken Pipe Error. This is
            fine, and expected behavior. We only want to connect to grab the TLS cert
        '''

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()

        # Check Initial state
        domains = self.get_table_rows("domains")
        self.assertEmpty(domains)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module.run([self.TEST_TARGET])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Domain Names found: 3")

        # Check real results
        domains = self.get_table_rows("domains")
        self.assertLengthEqual(domains, 3)

        domain_names = []
        for domain in domains:
            domain_names.append(domain[0])
        self.assertIn("test.example.com", domain_names)
        self.assertIn("api.example.com", domain_names)
        self.assertIn("localhost", domain_names)


