# =====================================================================================
# Imports: External
# =====================================================================================
import os
import json
import time
from urllib.parse import quote_plus
import requests.exceptions

from recon.sdk import BaseModule
from recon.sdk import utils
from recon.sdk.exceptions import ModuleRuntimeException
from recon.sdk.exceptions import ModuleValidationException
from .exceptions import APIRateLimitExceeded
from requests.exceptions import RequestException

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: GitHub Dorks Analyzer
# =====================================================================================
class Module(BaseModule):
    '''
    GitHub Gist Vulnerability Searcher Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    BASE_URL            = "https://api.github.com"
    THROTTLE_DURATION   = 6     # Currently only used for test purposes
    PAGE_SIZE           = 30    # Currently only used for test purposes

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def preflight(self):
        '''
        Override: Module prelight
        '''
        self._test_results_file = None # Used for Test Cases
        self._headers = None
        self._dorks = []
        return super().preflight()

    def module_pre(self):
        '''
        Override: Set up module properties and perform any additional validation
        '''

        # Options
        self._dorks_file_path   = self.get_option_value("DorksFile")
        self._page_limit        = self.get_option_value("PageLimit")

        # =====================================================================================
        # Load Dork Entries
        # =====================================================================================
        if not os.path.isfile(self._dorks_file_path):
            self._dorks_file_path = os.path.join(self.get_package_path(), self._dorks_file_path)
            if not os.path.isfile(self._dorks_file_path):
                raise ModuleValidationException(
                    "Could not load GitHub Dorks file. Check location is valid: %s" % self._dorks_file_path
                )

        with open(self._dorks_file_path) as dorks_file:
            for line in dorks_file.readlines():
                line = line.strip("\n")
                if line and line not in self._dorks and not line.startswith("#"):
                    self._dorks.append(line)

        # Check we actually have some keywords
        if not self._dorks:
            raise ModuleValidationException("Could not find any dorks in specified file")
        self.debug(f"{len(self._dorks)} Dork(s) loaded.")

        # Process Keys
        self._api_key = self.keys.get("github_api")

    def module_run(self, repos):
        '''
        Override: Module execution
        '''
        count = 0
        vulns_discovered = 0
        queries_count = len(repos) * len(self._dorks)
        self.alert("Warning: GitHub Search rate limiting has been enforced to prevent violation. Please be patient")

        # =====================================================================================
        # Iterate Repos
        # =====================================================================================
        try:
            with self.get_progress_bar(queries_count, unit="queries") as progress:
                for repo in repos:
                    # =====================================================================================
                    # Iterate Dorks
                    # =====================================================================================
                    for dork in self._dorks:
                        query = f"repo:{repo} {dork}"
                        progress.write(f"Query ({count + 1} of {queries_count}): {utils.truncate_string(query, 50)}")
                        page_no = 1
                        while page_no <= self._page_limit:
                            self.debug("Fetching page: %s" % page_no)

                            results = self.run_search(query, page_no)

                            # =====================================================================================
                            # Process Results
                            # =====================================================================================
                            for result in results:
                                vuln_data = {
                                    "reference": query,
                                    "example": result["html_url"],
                                    "category": "github_dork"
                                }
                                vulns_discovered += self.insert_vulnerabilities(**vuln_data)

                            # Throttle
                            time.sleep(self.THROTTLE_DURATION)

                            count += 1
                            progress.update()

                            # Handle Paging
                            if len(results) < self.PAGE_SIZE:
                                break
                            page_no += 1

        except APIRateLimitExceeded as ex:
            self.error(str(ex))
            return

        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Vulnerabilities discovered: %s" % vulns_discovered)
        self.output("Repositories processed: %s" % len(repos))


    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def run_search(self, query, page_no):
        '''
        Runs a GitHub search

        :param query: The search query to execute
        :type query: str
        :param page_no: The query page number
        :type page_no: int
        '''
        results = {}
        url = f"{self.BASE_URL}/search/code?q={query}&page={page_no}"

        # =====================================================================================
        # Send Request
        # =====================================================================================
        if self._test_results_file:
            with open(self._test_results_file, "r") as test_results_file:
                results = json.load(test_results_file)
        else:
            try:
                response = self.request("GET", url, headers=self.get_headers())
                results = response.json()
            # =====================================================================================
            # Exception Handler: Connection failure
            # =====================================================================================
            except RequestException as ex:
                raise ModuleRuntimeException("Unable to reach GitHub API: %s" % ex)

            # =====================================================================================
            # Check HTTP Response
            # =====================================================================================
            if response.status_code == 401:
                raise ModuleValidationException("Invalid authentication key. Please check key and try again")
            elif response.status_code == 403:
                raise APIRateLimitExceeded(
                    "API Rate Limit exceeded, please don't run this module too often. The GitHub API throttles "
                    "code searches to a maximum of 10 per minute."
                )
            elif response.status_code != 200:
                raise ModuleRuntimeException(
                    "Unexpected response when trying to perform a GitHub search: %s"
                    % response.status_code
                )

        return results["items"]

    def get_headers(self):
        '''
        Builds and returns the GitHub API headers

        :returns: The GitHub API headers
        :rtype: dict
        '''

        if not self._headers:
            self._headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer " + self._api_key
            }
        return self._headers
