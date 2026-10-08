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
# Module Class: GitHub Commit Snooper
# =====================================================================================
class Module(BaseModule):
    '''
    GitHub Commit Snooper Module
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
        self._test_results_file = None # Used for Test Cases
        self._headers = None
        return super().preflight()

    def module_pre(self):
        '''
        Override: Set up module properties and perform any additional validation
        '''

        # Process Options
        self._page_limit        = self.get_option_value("PageLimit")
        self._extract_author    = self.get_option_value("ExtractAuthor")
        self._extract_committer = self.get_option_value("ExtractCommitter")

        # Process Keys
        self._api_key = self.keys.get("github_api")

    def module_run(self, repos):
        '''
        Override: Module execution
        '''
        count = 0
        commits_processed = 0
        profiles_discovered = 0
        contacts_discovered = 0

        # =====================================================================================
        # Iterate Users
        # =====================================================================================
        with self.get_progress_bar(len(repos), unit="queries") as progress:
            for repo_info in repos:
                progress.write(f"Target ({count + 1} of {len(repos)}): {repo_info}")
                repo_owner = repo_info[0]
                repo_name = repo_info[1]

                # =====================================================================================
                # Process Commits
                # =====================================================================================
                commits = self.fetch_repo_commits(repo_name, repo_owner)
                for commit in commits:
                    # =====================================================================================
                    # Process Commit Author
                    # =====================================================================================
                    if self._extract_author:
                        author_account_data = commit["commit"]["author"]
                        author_commit_data  = commit["author"]

                        # Create Author Profile
                        if author_commit_data:
                            author_profile_data = {
                                "username": author_commit_data["login"],
                                "url": author_commit_data["html_url"],
                                "resource": "GitHub",
                                "category": "development"
                            }
                            profiles_discovered += self.insert_profiles(**author_profile_data)

                        # Create Author Contact
                        if author_account_data:
                            f_name, m_name, l_name = utils.parse_fullname(author_account_data["name"])
                            author_contact_data = {
                                "first_name": f_name,
                                "middle_name": m_name,
                                "last_name": l_name,
                                "email": author_account_data["email"],
                                "title": "GitHub Contributor"
                            }
                            contacts_discovered += self.insert_contacts(**author_contact_data)

                    # =====================================================================================
                    # Process Commit Committer
                    # =====================================================================================
                    if self._extract_committer:
                        committer_account_data = commit["commit"]["committer"]
                        committer_commit_data  = commit["committer"]

                        # Create Committer Profile
                        if committer_commit_data:
                            committer_profile_data = {
                                "username": committer_commit_data["login"],
                                "url": committer_commit_data["html_url"],
                                "resource": "GitHub",
                                "category": "development"
                            }
                            profiles_discovered += self.insert_profiles(**committer_profile_data)

                        # Create Committer Contact
                        if committer_account_data:
                            f_name, m_name, l_name = utils.parse_fullname(committer_account_data["name"])
                            committer_contact_data = {
                                "first_name": f_name,
                                "middle_name": m_name,
                                "last_name": l_name,
                                "email": committer_account_data["email"],
                                "title": "GitHub Contributor"
                            }
                            contacts_discovered += self.insert_contacts(**committer_contact_data)

                    commits_processed += 1

                count += 1
                progress.update()

        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Profiles discovered: %s" % profiles_discovered)
        self.output("Contacts discovered: %s" % contacts_discovered)
        self.output("Commits processed: %s" % commits_processed)


    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def fetch_repo_commits(self, repo_name, repo_owner):
        '''
        Retrieves commits for the specified repository

        :param repo_name: The name of the repository
        :type repo_name: str
        :param repo_owner: The owner of the repository
        :type repo_owner: str
        '''
        page_no = 1
        commits = []

        # =====================================================================================
        # Fetch Commit pages
        # =====================================================================================
        while page_no <= self._page_limit:
            self.debug("Fetching page: %s" % page_no)
            url = self.BASE_URL + f"/repos/{quote_plus(repo_owner)}/{quote_plus(repo_name)}/commits?page={page_no}"

            # =====================================================================================
            # Send Request
            # =====================================================================================
            if self._test_results_file:
                with open(self._test_results_file, "r") as results_file:
                    commits = json.load(results_file)
            else:
                try:
                    response = self.request("GET", url, headers=self.get_headers())
                    commits = response.json()
                # =====================================================================================
                # Exception Handler: JSON Parse Error
                # =====================================================================================
                except requests.exceptions.JSONDecodeError as ex:
                    self.debug("Bad API response: %s" % response.text)
                    raise ModuleValidationException("Unexpected response from GitHub API. Please check debug output")
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
                elif response.status_code != 200:
                    raise ModuleRuntimeException("Unexpected response from API: %s" % response.status_code)

            page_no += 1

        return commits

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
