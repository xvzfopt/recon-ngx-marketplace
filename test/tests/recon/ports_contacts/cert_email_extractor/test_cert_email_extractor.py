# =====================================================================================
# Imports: External
# =====================================================================================
import os
import time
import threading

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.sdk.exceptions import *
from module_test_case import ModuleTestCase

# =====================================================================================
# Base Test Case Class
# =====================================================================================
class TestCertEmailExtractor(ModuleTestCase):
    '''
    Tests the Cert Email Extractor Module
    '''

    '''
    TODO !
        - Add a note to say that connectionreseterror is fine and to be expected because of how we're using the connection
        - Add tests that actually check the data identified
        - Other bits of refactring and testing...
        - Then packgage up!
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY       = 1
    FQN             = "recon/ports-contacts/cert_email_extractor"
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
        contacts = self.get_table_rows("contacts")
        self.assertEmpty(contacts)

        # Execute Module
        self._recon.validate_options(self._module)
        self._module.preflight()
        self._module.run([self.TEST_TARGET])

        # Check Output
        self.assertInOutput(r".*Target \(1 of 1\).*")
        self.assertInOutput(r".*Email Addresses found: 3")

        # Check real results
        contacts = self.get_table_rows("contacts")
        self.assertLengthEqual(contacts, 3)

        emails_addresses = []
        for contact in contacts:
            emails_addresses.append(contact[3])
        self.assertIn("subject@example.com", emails_addresses)
        self.assertIn("san1@example.com", emails_addresses)
        self.assertIn("san2@example.com", emails_addresses)


