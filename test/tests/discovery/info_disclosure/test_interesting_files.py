# =====================================================================================
# Imports: External
# =====================================================================================
import os
import re
import time
from datetime import datetime

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.sdk.exceptions import *
from module_test_case import ModuleTestCase

# =====================================================================================
# Base Test Case Class
# =====================================================================================
class TestInterestingFilesFinder(ModuleTestCase):
    '''
    Tests the Interesting Files Finder Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    VERBOSITY = 1
    FQN = "discovery/info_disclosure/interesting_files"
    VERIFICATIONS_FILE      = os.path.join(ModuleTestCase.DATA_PATH, "interesting_files_verify.csv")
    TMP_VERIFICATIONS_FILE  = os.path.join(ModuleTestCase.TMP_PATH, "tmp_interesting_files_verify.csv")

    # =====================================================================================
    # General Methods
    # =====================================================================================
    def setUp(self):
        super(TestInterestingFilesFinder, self).setUp()

        # Set up Recon-NGX App
        self.set_up_recon_ngx()

        # Build Modules Paths
        mod_file_path = os.path.join(self.MODULES_PATH, "%s.py" % self.FQN)

        # Load Module
        self._module = self.load_module(self.FQN, mod_file_path)

    # =====================================================================================
    # Unit tests
    # =====================================================================================
    def test_successful_run(self):
        '''
        Tests successful execution of the Module
        '''
        self.clear_downloads_directory()
        self.assertEmpty(self.get_downloaded_files())

        # Set options
        self._recon.set_verbosity(2)
        options = self._module.get_options()
        options["csv_file"] = self.VERIFICATIONS_FILE
        # options["domains"] = self.TEST_DOMAINS_FILENAME

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])

        # Check At least one file was found
        regex = re.compile(r"\[200\] https://google.com:443/[^ ]* => '.*' found!")
        self.assertInOutput(regex)
        self.assertNotEmpty(self.get_downloaded_files())

        # Check at least one file was not found
        regex = re.compile(r"\[\*\] \[404\] https://google.com:443/[^ ]*")
        self.assertInOutput(regex)

    def test_connection_errors(self):
        '''
        Test Handling of connection errors
        '''

        # Set options
        options = self._module.get_options()
        options["csv_file"] = self.VERIFICATIONS_FILE
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()

        # =====================================================================================
        # Test - Unknown Domain Name - No errors thrown
        # =====================================================================================
        # Execute Module
        self._module.run(["fdsfdsfsdfdsjjjdsjfs883838d.com"])

        # =====================================================================================
        # Test - Connection Refused
        # =====================================================================================
        self._module.run(["127.0.0.1"])

    def test_option_csv_file(self):
        '''
        Tests the CSV_FILE option
        '''

        # =====================================================================================
        # Test - CSV_FILE not set
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["csv_file"] = ""
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual("Value required for the 'CSV_FILE' option.", cm)

        # =====================================================================================
        # Test - File does not exist
        # =====================================================================================
        self._recon.set_verbosity(2)
        # Set options
        options = self._module.get_options()
        options["csv_file"] = "/hello/fdf/122.txtff"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual(
            "Validation failed for the 'CSV_FILE' option => The specified path does not point to a valid"
            ", existing file",
            cm
        )

        # =====================================================================================
        # Test - Check the specified file was actually used
        # =====================================================================================
        # Create a new verifications file with some misc items
        file_name = "this_file_does_not_exist.txt"
        self._create_tmp_verifications([f"{file_name},testing123"])

        # Set options
        self._recon.set_verbosity(2)
        options = self._module.get_options()
        options["csv_file"] = self.TMP_VERIFICATIONS_FILE

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])

        # Check no files were found
        regex = re.compile(r"\[\*\] \[200\] https://google.com:443/%s => '%s' found!" % (file_name, file_name))
        self.assertNotInOutput(regex)

        # Explicitly check that our temp verification file was NOT found
        regex = re.compile(r"\[\*\] \[404\] https://google.com:443/%s" % file_name)
        self.assertInOutput(regex)

        # =====================================================================================
        # Test - Badly formatted CSV File
        # =====================================================================================
        self._recon.set_verbosity(1)
        # Create a new verifications file with some misc items
        if os.path.exists(self.TMP_VERIFICATIONS_FILE):
            os.remove(self.TMP_VERIFICATIONS_FILE)
        with open(self.TMP_VERIFICATIONS_FILE, "w") as tmp_verif_file:
            tmp_verif_file.write(f"This is going to trigger an exception because this is not valid CSV format for the module")

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])
        regex = re.compile(r"\[!\] Error parsing specified CSV_FILE")
        self.assertInOutput(regex)

    def test_option_download(self):
        '''
        Tests the DOWNLOAD option
        '''

        # =====================================================================================
        # Test - DOWNLOAD not set
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["csv_file"] = self.VERIFICATIONS_FILE
        options["download"] = ""
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual("Value required for the 'DOWNLOAD' option.", cm)

        # =====================================================================================
        # Test - DOWNLOAD not a valid Boolean
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["download"] = "dsds"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual("Validation failed for the 'DOWNLOAD' option => Not a valid boolean value", cm)

        # =====================================================================================
        # Test - DOWNLOAD set to False
        # =====================================================================================
        self.clear_downloads_directory()

        # Create tmp verifications file
        file_name = "robots.txt"
        options["csv_file"] = self.TMP_VERIFICATIONS_FILE
        self._create_tmp_verifications([f"{file_name},User-agent:"])

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()
        options["download"] = "false"

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])

        # Check not downloaded
        self.assertEmpty(self.get_downloaded_files())
        self.assertNotInOutput(r"\[\*\] Files downloaded to ")

        # =====================================================================================
        # Test - DOWNLOAD set to True
        # =====================================================================================
        self.clear_downloads_directory()

        # Create tmp verifications file
        file_name = "robots.txt"
        options["csv_file"] = self.TMP_VERIFICATIONS_FILE
        self._create_tmp_verifications([f"{file_name},User-agent:"])

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()
        options["download"] = "true"

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])

        # Check not downloaded
        self.assertLengthEqual(self.get_downloaded_files(), 1)
        self.assertEndsWith(self.get_downloaded_files()[0], "robots.txt")
        self.assertInOutput(r"\[\*\] Files downloaded to ")

    def test_protocol_option(self):
        '''
        Tests the PROTOCOL option
        '''

        # =====================================================================================
        # Test - PROTOCOL not set
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["csv_file"] = self.VERIFICATIONS_FILE
        options["protocol"] = ""
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual("Value required for the 'PROTOCOL' option.", cm)

        # =====================================================================================
        # Test - Not a valid HTTP protocol
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["csv_file"] = self.VERIFICATIONS_FILE
        options["protocol"] = "testing123"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual(
            "Validation failed for the 'PROTOCOL' option => Not a valid HTTP protocol (HTTP/HTTPS)",
            cm
        )

        # =====================================================================================
        # Test - HTTP protocol
        # =====================================================================================
        self.clear_downloads_directory()

        # Create tmp verifications file
        file_name = "robots.txt"
        options["csv_file"] = self.TMP_VERIFICATIONS_FILE
        options["protocol"] = "http"
        options["port"] = 80
        self._create_tmp_verifications([f"{file_name},User-agent:"])

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])

        # Check Output
        regex = re.compile(r"\[200\] http://google.com:80/%s => '%s' found!" % (file_name, file_name))
        self.assertInOutput(regex)

        # =====================================================================================
        # Test - HTTPS protocol
        # =====================================================================================
        self.clear_downloads_directory()

        # Create tmp verifications file
        options["protocol"] = "https"
        options["port"] = 443
        self._create_tmp_verifications([f"{file_name},User-agent:"])

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])

        # Check Output
        regex = re.compile(r"\[200\] https://google.com:443/%s => '%s' found!" % (file_name, file_name))
        self.assertInOutput(regex)

    def test_port_option(self):
        '''
        Tests the PORT option
        '''

        # =====================================================================================
        # Test - PORT not set
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["csv_file"] = self.VERIFICATIONS_FILE
        options["port"] = ""
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual("Value required for the 'PORT' option.", cm)

        # =====================================================================================
        # Test - Not a valid port number - Bad type
        # =====================================================================================
        # Set options
        options = self._module.get_options()
        options["csv_file"] = self.VERIFICATIONS_FILE
        options["port"] = "testing123"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual(
            "Validation failed for the 'PORT' option => Not a valid port number",
            cm
        )

        # =====================================================================================
        # Test - Not a valid port number - Out of range
        # =====================================================================================
        options["port"] = "-50"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual(
            "Validation failed for the 'PORT' option => Not a valid port number",
            cm
        )

        options["port"] = "65536"
        with self.assertRaises(ModuleValidationException) as cm:
            self._recon.validate_options(self._module.get_options())
        self.assertExceptionStringEqual(
            "Validation failed for the 'PORT' option => Not a valid port number",
            cm
        )

        # =====================================================================================
        # Test - Bad port number - Connection reset
        # =====================================================================================
        self.clear_downloads_directory()

        # Create tmp verifications file
        file_name = "robots.txt"
        options["csv_file"] = self.TMP_VERIFICATIONS_FILE
        options["port"] = 21
        self._create_tmp_verifications([f"{file_name},User-agent:"])

        # Set options
        self._recon.set_verbosity(2)
        options = self._module.get_options()

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])

        # Check Output
        regex = re.compile(r"\[\*\] Connection reset error: https://google.com:21/%s" % file_name)
        self.assertInOutput(regex)

        # =====================================================================================
        # Test - Port 80 (HTTP)
        # =====================================================================================
        self.clear_downloads_directory()

        # Create tmp verifications file
        options["protocol"] = "http"
        options["port"] = 80
        self._create_tmp_verifications([f"{file_name},User-agent:"])

        # Set options
        self._recon.set_verbosity(1)
        options = self._module.get_options()

        # Execute Module
        self._recon.validate_options(self._module.get_options())
        self._module.preflight()
        self._module.run(["google.com"])

        # Check Output
        regex = re.compile(r"\[200\] http://google.com:80/%s => '%s' found!" % (file_name, file_name))
        self.assertInOutput(regex)

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def _create_tmp_verifications(self, verifications):
        '''
        Creates a temporary verifications file with the specified entries. Provides a way to quickly run
        one or two file checks, instead of the default built in list

        :param verifications: list of verifications to add to the file
        :type verifications: list
        '''

        # Clear existing file
        if os.path.exists(self.TMP_VERIFICATIONS_FILE):
            os.remove(self.TMP_VERIFICATIONS_FILE)

        # Add entries
        with open(self.TMP_VERIFICATIONS_FILE, "w") as tmp_verif_file:
            for entry in verifications:
                tmp_verif_file.write(f"{entry}\n")

