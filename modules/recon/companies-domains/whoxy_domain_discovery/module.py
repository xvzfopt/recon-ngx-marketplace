# =====================================================================================

# Imports: External
# =====================================================================================
import json
import os.path
from urllib.parse import quote

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
# Module Class: Whoxy Domain Discovery
# =====================================================================================
class Module(BaseModule):
    '''
    Whoxy Domain Discovery Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    BASE_URL        = "https://api.whoxy.com"

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def preflight(self):
        '''
        Override: Module prelight
        '''
        self._test_results_file = None # Used for Test Cases
        self._account_balance = {}
        return super().preflight()

    def module_pre(self):
        '''
        Override: Set up module properties and perform any additional validation
        '''

        # Process Options
        self._page_limit = self.get_option_value("PageLimit")
        self._confirm_before_run = self.get_option_value("Confirm")

        # Process Keys
        self._api_key = self.keys.get("whoxy_api")

        # =====================================================================================
        # Check Account Balance
        # =====================================================================================
        if self.get_credits_remaining() <= 0:
            raise ModuleValidationException(
                "No Reverse Whois Lookup credits on this account. Please add credits to use this module"
            )

    def module_run(self, companies):
        '''
        Override: Module execution
        '''
        count = 0
        domains_found = 0

        # =====================================================================================
        # Check for sufficient credits
        # =====================================================================================
        if self.get_credits_remaining() < len(companies):
            raise ModuleValidationException(
                f"Query requires {len(companies)} credit(s), but there are only {self.get_credits_remaining()} available."
                f" Please add more credits to continue"
            )

        # =====================================================================================
        # Iterate Companies
        # =====================================================================================
        with self.get_progress_bar(len(companies), unit="queries") as progress:
            for company in companies:
                page_no = 1
                progress.write(f"Target ({count + 1} of {len(companies)}): {company}")

                while page_no <= self._page_limit:
                    self.debug("Fetching page: %s" % page_no)
                    # =====================================================================================
                    # Send Request
                    # =====================================================================================
                    if not self._test_results_file or not os.path.isfile(self._test_results_file):
                        try:
                            url = f"{self.BASE_URL}/?key={self._api_key}&reverse=whois&company={quote(company)}"
                            response = self.request("GET", url)
                            data = response.json()
                        except requests.exceptions.JSONDecodeError as ex:
                            self.debug("Bad API response: %s" % response.text)
                            raise ModuleRuntimeException("Unexpected response from API. Please check debug output")
                        except RequestException as ex:
                            raise ModuleRuntimeException("Unable to reach Whoxy API: %s" % ex)

                        # Check Response
                        if response.status_code != 200:
                            raise ModuleRuntimeException("Unexpected response from API: %s" % response.status_code)
                    else:
                        with open(self._test_results_file) as results_file:
                            data = json.load(results_file)

                    # =====================================================================================
                    # Process Data
                    # =====================================================================================
                    if data["total_results"] == 0:
                        break
                    for result in data.get("search_result", []):
                        domains_found += self.insert_domains(result["domain_name"])

                    # Check Paging
                    if data["current_page"] >= data["total_pages"]:
                        self.debug("Final page reached")
                        break
                    page_no += 1

                count += 1
                progress.update()

        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Domain Names found: %s" % domains_found)

        # =====================================================================================
        # Print API Account Data
        # =====================================================================================
        self._account_balance = self.fetch_account_balance()
        self.heading("Whoxy API Status", level=0)
        self.output("Credits Remaining: %s" % self.get_credits_remaining())

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def get_credits_remaining(self):
        '''
        Gets the number of remaining credits for Reverse Whois Lookups

        :returns: The number of monthly credits remaining on the account, specifically for Reverse Whois Lookups
        :rtype: int
        '''
        remaining = 0

        # Fetch Account Balance
        if not self._account_balance:
            self._account_balance = self.fetch_account_balance()

        # Get Monthly account
        remaining = self._account_balance.get("reverse_whois_balance", 0)

        return remaining

    def fetch_account_balance(self):
        '''
        Gets the API account information
        '''

        # =====================================================================================
        # Send Request
        # =====================================================================================
        try:
            url = f"{self.BASE_URL}/?key={self._api_key}&account=balance"
            response = self.request("GET", url)
            r_data = response.json()

            # Check Response
            if r_data["status"] == 0:
                raise ModuleRuntimeException(f"Whoxy API Error: {r_data['status_reason']}")
        except RequestException as ex:
            raise ModuleRuntimeException("Unable to Reach Whoxy API: %s" % ex)

        # =====================================================================================
        # Process Response
        # =====================================================================================
        if response.status_code != 200:
            raise ModuleRuntimeException("Unexpected response from API: %s" % response.status_code)

        return r_data


