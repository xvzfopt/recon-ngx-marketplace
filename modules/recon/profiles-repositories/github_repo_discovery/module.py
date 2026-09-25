# =====================================================================================

# Imports: External
# =====================================================================================
import json
from urllib.parse import quote_plus
import requests.exceptions
from recon.sdk import BaseModule
from recon.sdk import utils
from recon.sdk.exceptions import ModuleRuntimeException
from recon.sdk.exceptions import ModuleValidationException
from requests.exceptions import RequestException

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: GitHub Repo Discovery
# =====================================================================================
class Module(BaseModule):
    '''
    GitHub Repo Discovery Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    BASE_URL        = "https://api.github.com"

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def preflight(self):
        '''
        Override: Module prelight
        '''
        self._test_results_file_repos = None # Used for Test Cases
        self._test_results_file_gists = None # Used for Test Cases
        self._headers = None
        return super().preflight()

    def module_pre(self):
        '''
        Override: Set up module properties and perform any additional validation
        '''

        # Process Options
        self._ignore_forks = self.get_option_value("IgnoreForks")
        self._page_limit = self.get_option_value("PageLimit")

        # Process Keys
        self._api_key = self.keys.get("github_api")

    def module_run(self, usernames):
        '''
        Override: Module execution
        '''
        count = 0
        repos_discovered = 0
        gists_discovered = 0

        # =====================================================================================
        # Iterate Users
        # =====================================================================================
        with self.get_progress_bar(len(usernames), unit="queries") as progress:
            for username in usernames:
                progress.write(f"Target ({count + 1} of {len(usernames)}): {username}")

                repos_discovered += self.discover_repos(username)
                gists_discovered += self.discover_gists(username)
                count += 1
                progress.update()

        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Repositories discovered: %s" % repos_discovered)
        self.output("Gists discovered: %s" % gists_discovered)
        self.output("Users processed: %s" % count)

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def discover_repos(self, username):
        '''
        Discovers repositories associated with the specified username

        :param username: The target username
        :type username: str
        :returns: The number of discovered repos
        :rtype: int
        '''
        page = 1
        count = 0

        # =====================================================================================
        # Page Lookups
        # =====================================================================================
        while page <= self._page_limit:
            url = f"{self.BASE_URL}/users/{quote_plus(username)}/repos?page={page}"
            self.debug("Fetching page: %s" % page)

            if self._test_results_file_repos:
                with open(self._test_results_file_repos, "r") as results_file:
                    results = json.load(results_file)
            else:
                try:
                    response = self.request("GET", url, headers=self.get_headers())
                    results = response.json()
                except requests.exceptions.JSONDecodeError as ex:
                    self.debug("Bad API response: %s" % response.text)
                    raise ModuleValidationException("Unexpected response from GitHub API. Please check debug output")
                except RequestException as ex:
                    raise ModuleRuntimeException("Unable to reach GitHub API: %s" % ex)

                # Check Response
                if response.status_code == 401:
                    raise ModuleValidationException("Invalid authentication key. Please check key and try again")
                elif response.status_code != 200:
                    raise ModuleRuntimeException("Unexpected response from API: %s" % response.status_code)

            # =====================================================================================
            # Process Data
            # =====================================================================================
            if not results:
                break
            for result in results:
                if self._ignore_forks and result["fork"]:
                    self.debug("Ignoring fork")
                    continue
                repo_data = {
                    "name": result["name"],
                    "owner": result["owner"]["login"],
                    "description": result["description"],
                    "url": result["url"],
                    "resource": "GitHub",
                    "category": "repo"
                }
                count += self.insert_repositories(**repo_data)
            page += 1

        return count

    def discover_gists(self, username):
        '''
        Discovers gists associated with the specified username

        :param username: The target username
        :type username: str
        :returns: The number of discovered gists
        :rtype: int
        '''
        page = 1
        count = 0

        # =====================================================================================
        # Page Lookups
        # =====================================================================================
        while page <= self._page_limit:
            url = f"{self.BASE_URL}/users/{quote_plus(username)}/gists?page={page}"
            self.debug("Fetching page: %s" % page)

            if self._test_results_file_gists:
                with open(self._test_results_file_gists, "r") as results_file:
                    results = json.load(results_file)
            else:
                try:
                    response = self.request("GET", url, headers=self.get_headers())
                    results = response.json()
                except requests.exceptions.JSONDecodeError as ex:
                    self.debug("Bad API response: %s" % response.text)
                    raise ModuleValidationException("Unexpected response from GitHub API. Please check debug output")
                except RequestException as ex:
                    raise ModuleRuntimeException("Unable to reach GitHub API: %s" % ex)

                # Check Response
                if response.status_code == 401:
                    raise ModuleValidationException("Invalid authentication key. Please check key and try again")
                elif response.status_code != 200:
                    raise ModuleRuntimeException("Unexpected response from API: %s" % response.status_code)

            # =====================================================================================
            # Process Data
            # =====================================================================================
            if not results:
                break
            for result in results:
                files = result["files"].values()
                for _file in files:
                    gist_data = {
                        "name": _file["filename"],
                        "owner": result["owner"]["login"],
                        "description": result["description"],
                        "url": _file["raw_url"],
                        "resource": "GitHub",
                        "category": "gist"
                    }
                    count += self.insert_repositories(**gist_data)
            page += 1

        return count

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
