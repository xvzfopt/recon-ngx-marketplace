# =====================================================================================
# Imports: External
# =====================================================================================
import os
import re
from recon.sdk import BaseModule
from recon.sdk import utils
from recon.sdk.exceptions import ModuleRuntimeException
from requests.exceptions import RequestException

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: IANA PEN Domain names Extractor
# =====================================================================================
class Module(BaseModule):
    '''
    IANA PEN Domain Names Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    URL = 'https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers'

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def preflight(self):
        '''
        Override: Module prelight
        '''
        self._test_results_file = None # Used for Test Cases
        return super().preflight()

    def module_pre(self):
        '''
        Override: Set up module properties and perform any additional validation
        '''
        pass

    def module_run(self, companies):
        '''
        Override: Module execution
        '''

        # =====================================================================================
        # Iterate Target Companies
        # =====================================================================================
        count = 0
        domains_found = 0

        # =====================================================================================
        # Fetch Registry
        # =====================================================================================
        registry = self.fetch_registry_contents()

        with self.get_progress_bar(len(companies), unit="queries") as progress:
            for company in companies:
                progress.write(f"Target ({count + 1} of {len(companies)}): {company}")

                # Extract Contact information
                comp = re.escape(company)
                pattern = r'(\d+)\s*\n\s{2}.*' + comp + r'.*\s*\n\s{4}(.*)\s*\n\s{6}(.*)\s*\n'
                matches = 0

                # Find matches. Add contacts
                for match in re.finditer(pattern, registry, re.IGNORECASE):
                    matches += 1

                    # Extract Domain Name
                    domain = match.groups()[2].split("&")[1]

                    # Insert Domain Name
                    domains_found += self.insert_domains(domain)

                count += 1
                progress.update()

        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Domain Names found: %s" % domains_found)

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def fetch_registry_contents(self):
        '''
        Fetches the contents of the IANA PEN Registry

        :returns: The registry contents
        :rtype: str
        '''
        content = None

        # =====================================================================================
        # Load from Test File
        # =====================================================================================
        if self._test_results_file and os.path.isfile(self._test_results_file):
            with open(self._test_results_file) as registry_file:
                content = registry_file.read()

        # =====================================================================================
        # Fetch from IANA
        # =====================================================================================
        else:
            try:
                response = self.request("GET", self.URL)
                if not response.status_code == 200:
                    raise ModuleRuntimeException("Unable to fetch IANA PEN Registry: %s" % response.status_code)

                # Process Contents
                content = response.text
                if not content.startswith("PRIVATE ENTERPRISE NUMBERS"):
                    self.debug("IANA PEN Registry response: %s" % content)
                    raise ModuleRuntimeException("Unexpected data received from IANA PEN registry")
            except RequestException as ex:
                self.error("Unable to reach IANA PEN Registry")
                raise


        return content
