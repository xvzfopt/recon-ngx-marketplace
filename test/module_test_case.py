# =====================================================================================
# Imports: External
# =====================================================================================
import os
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
    DATA_PATH               = os.path.join(MARKETPLACE_PATH, 'data')
    TEST_DATA_PATH          = os.path.join(MARKETPLACE_PATH, "test", "data")
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
            self.MODULES_PATH, self.TEST_DATA_PATH
        )
        self._recon.set_workspace(self.WORKSPACE_NAME, False)
        self._console = self._recon.get_console()

    # =====================================================================================
    # Custom Assertions
    # =====================================================================================
    def assertInOutput(self, pattern, message=None):
        '''
        Checks that a line matching the specified Regex was found in the Console Output

        :param pattern: The Regex pattern to check for
        :type pattern: Pattern
        '''
        match = False

        for line in self._console.get_output():
            match = re.match(pattern, line)
            if match:
                break

        if not match:
            raise AssertionError(message)

    def assertNotInOutput(self, pattern, message=None):
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
            raise AssertionError(message)

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

        module = utils.load_file_module(load_name, path)
        sys.modules[load_name] = module

        # Create Module Instance
        mod_instance = module.Module(mod_name, fqn, self._recon)

        return mod_instance


