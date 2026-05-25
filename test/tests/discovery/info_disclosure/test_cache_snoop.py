# =====================================================================================
# Imports: External
# =====================================================================================
import os
import re

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.sdk.exceptions import *
from module_test_case import ModuleTestCase

# =====================================================================================
# Base Test Case Class
# =====================================================================================
class TestDNSCacheSnoop(ModuleTestCase):
    '''
    Tests the DNS Cache Snoop Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 2
    FQN = "discovery/info_disclosure/cache_snoop"
    TEST_DOMAINS_FILENAME = "dns_cache_snoop_domains.txt"
    TEST_DOMAINS_PATH     = os.path.join(ModuleTestCase.DATA_PATH, TEST_DOMAINS_FILENAME)

    # =====================================================================================
    # General Methods
    # =====================================================================================
    def setUp(self):
        super(TestDNSCacheSnoop, self).setUp()

        # Set up Recon-NGX App
        self.set_up_recon_ngx()

        # Build Modules Paths
        mod_file_path = os.path.join(self.MODULES_PATH, "%s.py" % self.FQN)

        # Load Module
        self._module = self.load_module(self.FQN, mod_file_path)

        # Peform any additional setup
        self.delete_domains_files()

    # =====================================================================================
    # Unit tests
    # =====================================================================================
    def test_successful_run(self):
        '''
        Tests successful execution of the Module
        '''

        # Set options
        options = self._module.get_options()
        options["nameserver"] = "8.8.8.8"
        options["domains"] = self.TEST_DOMAINS_FILENAME

        # Add some domains to the domain names file
        test_domains = ["google.com", "x.com", "misc123sdd.com", "rt.com"]
        for test_domain in test_domains:
            self.add_domains_to_domains_file(test_domain)

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run([])

        # Check output for success
        for test_domain in test_domains:
            regex = re.compile(r"\[.\] %s => (Snooped!|Not Found.)\n" % test_domain)
            self.assertInOutput(
                regex,
                "Could not find a Domain snoop attempt for %s. Verbosity level is too low, or a module "
                "error occurred." % test_domain
            )

    def test_option_nameserver(self):
        '''
        Tests the NAMESERVER option
        '''

        # =====================================================================================
        # Test - Nameserver not set
        # =====================================================================================
        # Set options
        options = self._module.get_options()

        # Execute Module
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertEqual(str(cm.exception), "Value required for the 'NAMESERVER' option.")

        # =====================================================================================
        # Test - Nameserver empty
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["NAMESERVER"] = ""

        # Execute Module
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertEqual(str(cm.exception), "Value required for the 'NAMESERVER' option.")

        # =====================================================================================
        # Test - Nameserver not a valid IP (1)
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["NAMESERVER"] = "hello"

        # Execute Module
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertEqual(str(cm.exception), "Validation failed for the 'NAMESERVER' option => Not a valid IPv4 Address")

        # =====================================================================================
        # Test - Nameserver not a valid IP (2)
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["NAMESERVER"] = "8.8.8.257"

        # Execute Module
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertEqual(str(cm.exception), "Validation failed for the 'NAMESERVER' option => Not a valid IPv4 Address")

    def test_options_domains_file(self):
        '''
        Tests the DOMAINS option
        '''
        # =====================================================================================
        # Test - Domains file empty
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["NAMESERVER"] = "8.8.8.8"
        options["DOMAINS"] = ""

        # Execute Module
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertEqual(str(cm.exception), "Value required for the 'DOMAINS' option.")

        # =====================================================================================
        # Test - Domains file not found
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["NAMESERVER"] = "8.8.8.8"
        options["DOMAINS"] = "does_not_exist.txt"

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run([])
        self.assertInOutput(re.compile(r"\[!\] The specified domains file could not be found"))

    # =====================================================================================
    # Test Helpers
    # =====================================================================================
    def delete_domains_files(self):
        '''
        Deletes the temporary domains files
        '''
        if os.path.isfile(self.TEST_DOMAINS_PATH):
            os.remove(self.TEST_DOMAINS_PATH)

    def add_domains_to_domains_file(self, domain):
        '''
        Adds a domain name to the temporary domain names file

        :param domain: The domain name to add
        :type domain: str
        '''
        with open(self.TEST_DOMAINS_PATH, "a") as domains_file:
            domains_file.write("%s\n" % domain)