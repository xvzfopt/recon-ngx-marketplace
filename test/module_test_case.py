# =====================================================================================
# Imports: External
# =====================================================================================
import os
import shutil
import sys
import re
import importlib.util
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
    # Properties
    # =====================================================================================
    APP_AUTHOR          = 'xvzf_opt'
    VERBOSITY           = 2
    CHECK_VERSION       = False
    MARKETPLACE_ENABLED = False
    ACCESSIBLE          = False

    # Paths
    TOP_LEVEL_PATH          = Path(__file__).resolve().parent.parent.parent
    FRAMEWORK_PATH          = os.path.join(TOP_LEVEL_PATH, "recon-ngx")
    MARKETPLACE_PATH        = os.path.join(TOP_LEVEL_PATH, 'recon-ngx-marketplace')
    MODULES_PATH            = os.path.join(MARKETPLACE_PATH, 'modules')
    TMP_PATH                = os.path.join(MARKETPLACE_PATH, "test", "tmp")
    FRAMEWORK_VERSION_PATH  = os.path.join(FRAMEWORK_PATH, "VERSION")

    # Workspace Settings
    WORKSPACE_NAME      = "test"

    # =====================================================================================
    # Functions
    # =====================================================================================
    def setUp(self):
        '''
        Sets up the test environment.
        '''
        self._recon = None
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
            self.MODULES_PATH
        )
        self._recon.set_workspace(self.WORKSPACE_NAME, False)
        self._console = self._recon.get_console()

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
            raise AssertionError("Expected pattern matched output: %s" % pattern)

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


