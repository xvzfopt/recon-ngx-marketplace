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
# Module Class: GitHub User Miner
# =====================================================================================
class Module(BaseModule):
    '''
    GitHub User Miner Module
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
        self._test_results_file = None
        self._headers = None
        return super().preflight()

    def module_pre(self):
        '''
        Override: Set up module properties and perform any additional validation
        '''

        # Process Keys
        self._api_key = self.keys.get("github_api")

    def module_run(self, usernames):
        '''
        Override: Module execution
        '''
        count = 0
        contacts_created = 0

        # =====================================================================================
        # Iterate Companies
        # =====================================================================================
        with self.get_progress_bar(len(usernames), unit="queries") as progress:
            for username in usernames:
                progress.write(f"Target ({count + 1} of {len(usernames)}): {username}")

                # Build URL
                url = f"{self.BASE_URL}/users/{quote_plus(username)}"

                if self._test_results_file:
                    with open(self._test_results_file, "r") as results_file:
                        result = json.load(results_file)
                else:
                    try:
                        response = self.request("GET", url, headers=self.get_headers())
                        result = response.json()
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
                if not result:
                    break

                f_name, m_name, l_name = utils.parse_fullname(result.get("name") or "")
                title = "GitHub Contributor"
                if result["company"]:
                    title += f" at {result['company']}"
                contact_data = {
                    "first_name": f_name,
                    "middle_name": m_name,
                    "last_name": l_name,
                    "email": result["email"],
                    "region": result["location"],
                    "notes": f"Bio: {result['bio']}",
                    "title": title
                }
                contacts_created += self.insert_contacts(**contact_data)
                count += 1

                progress.update()

        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Contacts created: %s" % contacts_created)

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
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
