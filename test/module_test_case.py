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
    DATA_PATH               = os.path.join(MARKETPLACE_PATH, "test", "data")
    TMP_PATH                = os.path.join(MARKETPLACE_PATH, "test", "tmp")
    FRAMEWORK_VERSION_PATH  = os.path.join(FRAMEWORK_PATH, "VERSION")

    # Workspace Settings
    WORKSPACE_NAME      = "test"


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
            self.MODULES_PATH, self.DATA_PATH
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

        # Load Module spec file
        spec = importlib.util.spec_from_file_location(load_name, path)

        # Import module from spec
        module = importlib.util.module_from_spec(spec)
        sys.modules[load_name] = module

        # Create Module Instance
        spec.loader.exec_module(module)
        mod_instance = module.Module(mod_name, fqn, self._recon)

        return mod_instance


