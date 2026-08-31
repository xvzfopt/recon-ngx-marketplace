# =====================================================================================
# Imports: External
# =====================================================================================
import os
import shutil
import sys
import re
import yaml
import http.server
import ssl
import time
from threading import Thread
from pathlib import Path
from unittest import TestCase

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.core import ReconNGXApp
from recon.utils import utils

# =====================================================================================
# Base Test Case Class
# =====================================================================================
class ModuleTestCase(TestCase):
    '''
    Abstract Base Test Case Class. To be used as the base class for all Recon-NGX Module test cases.
    Not to be instantiated directly.
    '''

    # =====================================================================================
    # Properties: General
    # =====================================================================================
    APP_AUTHOR          = 'xvzf_opt'
    VERBOSITY           = 2
    CHECK_VERSION       = False
    MARKETPLACE_ENABLED = False
    ACCESSIBLE          = False
    MARKETPLACE_BRANCH  = "master"

    # =====================================================================================
    # Propertes: Paths
    # =====================================================================================
    TOP_LEVEL_PATH          = Path(__file__).resolve().parent.parent.parent
    FRAMEWORK_PATH          = os.path.join(TOP_LEVEL_PATH, "recon-ngx")
    MARKETPLACE_PATH        = os.path.join(TOP_LEVEL_PATH, 'recon-ngx-marketplace')
    MODULES_PATH            = os.path.join(MARKETPLACE_PATH, 'modules')
    TMP_PATH                = os.path.join(MARKETPLACE_PATH, "test", "tmp")
    DATA_PATH               = os.path.join(MARKETPLACE_PATH, "test", "data")
    FRAMEWORK_VERSION_PATH  = os.path.join(FRAMEWORK_PATH, "VERSION")

    KEYS_FILE_PATH          = os.path.join(DATA_PATH, "keys.yaml")
    KEYS_DB_PATH            = os.path.join(TMP_PATH, "keys.db")

    # =====================================================================================
    # Properties: Workspace
    # =====================================================================================
    WORKSPACE_NAME      = "_internal_test"

    # =====================================================================================
    # Set Up Functions
    # =====================================================================================
    def setUp(self):
        '''
        Sets up the test environment.
        '''
        self._recon = None
        self._httpd = None
        super(ModuleTestCase, self).setUp()

    def set_up_recon_ngx(self):
        '''
        Sets up the Recon-NGX app
        '''
        self._recon = ReconNGXApp(
            utils.get_version_number(self.FRAMEWORK_VERSION_PATH),
            self.APP_AUTHOR,
            self.VERBOSITY, self.CHECK_VERSION,
            self.MARKETPLACE_ENABLED,
            self.ACCESSIBLE,
            self.MODULES_PATH,
            self.MARKETPLACE_BRANCH
        )
        self._recon.set_workspace(self.WORKSPACE_NAME, False)
        self.get_workspace_db().clear_tables()
        self._console = self._recon.get_console()

        # =====================================================================================
        # Load Test Keys
        # =====================================================================================
        key_manager = self._recon.get_key_manager()
        key_manager.initialise_db(self.KEYS_DB_PATH)

        # Check Keys file
        if not os.path.isfile(self.KEYS_FILE_PATH):
            self._console.alert("Test Keys File was not found and will be created")
            self._console.alert("Make sure to set API keys for test case usage in %s" % self.KEYS_FILE_PATH)
            with open(self.KEYS_FILE_PATH, "w") as keys_file:
                yaml.safe_dump({"example_key": "Example"}, keys_file)

        # Read and Apply Keys
        with open(self.KEYS_FILE_PATH, "r") as keys_file:
            keys = yaml.safe_load(keys_file)
            for key in keys:
                key_manager.add_key(key, keys[key])

    def setUpHTTPServer(self, host="localhost", port=6767, certfile=None, keyfile=None):
        '''
        Set up an HTTP Server instance

        :param host: The hostname/IP address on which to bind the server. Defaults to localhost
        :type host: str, Optional
        :param port: The port on which to bind the server. Defaults to 6767
        :type port: int, Optional
        :param certfile: The path to the certificate file, if serving over HTTPS. Defaults to None (HTTP)
        :type certfile: str, Optional
        :param keyfile: The path to the key file, if serving over HTTPS. Defaults to None (HTTP)
        :type keyfile: str, Optional
        '''
        Thread(target=self._start_http_server_thread, daemon=True, kwargs={
            "host": host,
            "port": port,
            "certfile": certfile,
            "keyfile": keyfile
        }).start()

        # Give server chance to spin up
        time.sleep(1)

    # =====================================================================================
    # Tear Down Functions
    # =====================================================================================
    def tearDown(self):
        '''
        Module Test Case tear down function
        '''
        if self._httpd:
            self.tearDownHTTPServer()

    def tearDownHTTPServer(self):
        '''
        Tears down the HTTP Server instance
        '''
        self._httpd.shutdown()
        self._httpd.server_close()

    # =====================================================================================
    # Custom Assertions
    # =====================================================================================
    def assertEmpty(self, container):
        '''
        Asserts that the provided container is empty

        :param container: The container to check
        :type container: any
        '''
        if len(container) > 0:
            raise AssertionError("Expected container to be empty, but it has %s element(s)" % len(container))

    def assertNotEmpty(self, container):
        '''
        Asserts that the provided container is Not empty

        :param container: The container to check
        :type container: any
        '''
        if len(container) <= 0:
            raise AssertionError("Expected container to not be empty")

    def assertLengthEqual(self, item, length):
        '''
        Checks that the specified item or container is of the specified length

        :param item: The item to check
        :type item: any
        :param length: The expected length
        :type length: int
        '''
        if len(item) != length:
            raise AssertionError("Expected item to have length of %s, but got %s" % (length, len(item)))

    def assertStartsWith(self, string, prefix):
        '''
        Checks that the provided string startswith the specified prefix

        :param string: The string to check
        :type string: str
        :param suffix: The expected suffix
        :type suffix: str
        '''
        if not string.startswith(prefix):
            raise AssertionError("String does not start with '%s': %s" % (prefix, string))

    def assertEndsWith(self, string, suffix):
        '''
        Checks that the provided string endswith the specified suffix

        :param string: The string to check
        :type string: str
        :param suffix: The expected suffix
        :type suffix: str
        '''
        if not string.endswith(suffix):
            raise AssertionError("String does not end with '%s': %s" % (suffix, string))

    def assertInOutput(self, pattern):
        '''
        Checks that a line matching the specified Regex was found in the Console Output

        :param pattern: The Regex pattern to check for
        :type pattern: Pattern
        '''
        match = False

        for line in self._console.get_output():
            line = utils.ansi_clean(line)
            match = re.match(pattern, line)
            if match:
                break

        if not match:
            raise AssertionError("Expected pattern did not match output: %s" % pattern)

    def assertNotInOutput(self, pattern):
        '''
        Checks that a line matching the specified Regex was NOT found in the Console Output

        :param pattern: The Regex pattern to check for
        :type pattern: Pattern
        '''
        match = False

        for line in self._console.get_output():
            match = re.match(pattern, line)
            if match:
                break

        if match:
            raise AssertionError("Unexpected pattern matched output: %s" % pattern)

    def assertExceptionStringEqual(self, expected, cm):
        '''
        Asserts that the exception string of the caught exception is equal to the expected stirng

        :param expected: The expected exception string
        :type expected: str
        :param cm: The ContextManager instance (from with self.assertRaises() as cm)
        :type cm: ContextManager
        '''

        exception_string = str(cm.exception)
        if expected != exception_string:
            raise AssertionError("Expected exception string to be '%s', but got '%s'" % (expected, exception_string))

    # =====================================================================================
    # Helpers
    # =====================================================================================
    def get_workspace_downloads_path(self):
        '''
        Gets the path to the workspace downloads directory

        :returns: The path to the workspace downloads directory
        :rtype: str
        '''
        path = None
        if self._recon:
            path = self._recon.get_current_workspace().get_downloads_path()
        return path

    def get_workspace_db(self):
        '''
        Gets the current Workspace Database

        :returns: The DB of the current workspace
        :rtype: WorkspaceDB
        '''
        return self._recon.get_current_workspace().get_db()

    def get_table_rows(self, table_name):
        '''
        Gets all rows in the specified table

        :param table_name: The table to get rows for
        :type table_name: str
        :returns: A list of results
        :rtype: list
        '''
        return self.get_workspace_db().query("SELECT * FROM %s" % table_name)

    def clear_downloads_directory(self):
        '''
        Clears all files in the workspace downloads directory
        '''
        path = self.get_workspace_downloads_path()
        if path:
            shutil.rmtree(path)
            os.makedirs(path)

    def get_downloaded_files(self):
        '''
        Gets a list of downloaded files from the workspace downloads directory

        :returns: A list of downloaded files for the current Workspace
        :rtype: list
        '''
        path = self.get_workspace_downloads_path()
        if path and os.path.isdir(path):
            return os.listdir(path)
        return []


    def load_module(self, fqn, path):
        '''
        Loads a Recon-NGX Module and returns an instance of it

        :param fqn: The Fully-Qualified Name (FQN) of the module
        :type fqn: str
        :param path: The path to the module file
        :type path: str
        :returns: The module instance
        :rtype: BaseModule
        '''

        # Process Module from FQN
        mod_name = fqn.split("/")[-1]
        load_name = fqn.replace("/", "_")

        module = utils.load_package_module(load_name, path)
        sys.modules[load_name] = module

        # Create Module Instance
        mod_instance = module.Module(mod_name, fqn, self._recon)

        return mod_instance

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
    def _start_http_server_thread(self, host="localhost", port=6767, certfile=None, keyfile=None):
        '''
        Start the HTTP Server Thread

        :param host: The hostname/IP address on which to bind the server. Defaults to localhost
        :type host: str, Optional
        :param port: The port on which to bind the server. Defaults to 6767
        :type port: int, Optional
        :param certfile: The path to the certificate file, if serving over HTTPS. Defaults to None (HTTP)
        :type certfile: str, Optional
        :param keyfile: The path to the key file, if serving over HTTPS. Defaults to None (HTTP)
        :type keyfile: str, Optional
        '''
        server_address = (host, port)

        # =====================================================================================
        # Initialise server
        # =====================================================================================
        self._httpd = http.server.HTTPServer(
            server_address,
            http.server.SimpleHTTPRequestHandler
        )

        # =====================================================================================
        # Set up TLS
        # =====================================================================================
        if certfile and keyfile:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

            context.load_cert_chain(
                certfile=certfile,
                keyfile=keyfile
            )

            self._httpd.socket = context.wrap_socket(
                self._httpd.socket,
                server_side=True
            )

        self._httpd.serve_forever()


