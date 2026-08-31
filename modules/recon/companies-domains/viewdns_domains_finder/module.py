# =====================================================================================

# Imports: External
# =====================================================================================
import json
import os.path

from recon.sdk import BaseModule
from recon.sdk import utils
from recon.sdk.exceptions import ModuleRuntimeException
from recon.sdk.exceptions import ModuleValidationException
from requests.exceptions import RequestException

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: ViewDNS Domains Finder
# =====================================================================================
class Module(BaseModule):
    '''
    ViewDNS Domains Finder Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    BASE_URL        = "https://api.viewdns.info"
    EP_REVERSEWHOIS = "/reversewhois"
    EP_ACCOUNT      = "/account"

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

        # Process Keys
        self._api_key = self.keys.get("viewdns_api")

        # Check Account Balance
        self.validate_account_balance()

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
        # Iterate Companies
        # =====================================================================================
        with self.get_progress_bar(len(companies), unit="queries") as progress:
            for company in companies:
                progress.write(f"Target ({count + 1} of {len(companies)}): {company}")

                # =====================================================================================
                # Send Request
                # =====================================================================================
                if not self._test_results_file or not os.path.isfile(self._test_results_file):
                    try:
                        url = f"{self.BASE_URL}/{self.EP_REVERSEWHOIS}?q={company}&apikey={self._api_key}&output=json"
                        response = self.request("GET", url)
                    except RequestException as ex:
                        raise ModuleRuntimeException("Unable to reach ViewDNS API: %s" % ex)

                    # Check Response
                    if response.status_code != 200:
                        raise ModuleRuntimeException("Unexpected response from API: %s" % response.status_code)

                    # Process data
                    data = response.json()
                else:
                    with open(self._test_results_file) as results_file:
                        data = json.load(results_file)

                # Process Data
                for match in data["response"]["matches"]:
                    self.insert_domains(match["domain"])
                    domains_found += 1

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
    def validate_account_balance(self, count=1):
        '''
        Checks that the API account has sufficient balance to perform the specified number of queries

        :param count: The number of queries that will be performed
        :type count: int
        :raises: ModuleValidatingException if account balance is insufficient
        '''

        # Fetch Account Balance
        if not self._account_balance:
            self._account_balance = self.fetch_account_balance()

        # Check Account Balance
        if self.get_monthly_remaining_credits() < count and self.get_prepaid_remaining_credits() < count:
            if self.is_trial_account():
                raise ModuleValidationException(
                    "This module does not support ViewDNS trial accounts. Please upgrade to a paid plan and try again"
                )
            else:
                raise ModuleValidationException(
                    "Insufficient balance. Please adjust your paid plan, try again later, or purchase prepaid credits"
                )

    def is_trial_account(self):
        '''
        Checks if the connected API account is a trial account

        :returns: True if the account is a trial account
        :rtype: bool
        '''

        # Fetch Account Balance
        if not self._account_balance:
            self._account_balance = self.fetch_account_balance()

        # Check for Trial
        if "trial" in self._account_balance or "monthly" not in self._account_balance:
            return True
        return False

    def get_prepaid_remaining_credits(self):
        '''
        Gets the number of remaining prepaid credits

        :returns: The number of prepaid credits remaining on the account
        :rtype: int
        '''

        # Fetch Account Balance
        if not self._account_balance:
            self._account_balance = self.fetch_account_balance()

        return max(0, int(self._account_balance["prepaid"]["balance"]))

    def get_monthly_remaining_credits(self):
        '''
        Gets the number of remaining monthly credits

        :returns: The number of monthly credits remaining on the account
        :rtype: int
        '''
        remaining = 0

        # Fetch Account Balance
        if not self._account_balance:
            self._account_balance = self.fetch_account_balance()

        # Get Monthly account
        if "monthly" in self._account_balance:
            remaining = int(self._account_balance["monthly"]["limit"]) - int(self._account_balance["monthly"]["usage"])
            remaining = max(0, remaining)

        return remaining

    def fetch_account_balance(self):
        '''
        Gets the API account information
        '''

        # =====================================================================================
        # Send Request
        # =====================================================================================
        try:
            url = f"{self.BASE_URL}/{self.EP_ACCOUNT}?action=balance&apikey={self._api_key}&output=json"
            response = self.request("GET", url)
        except RequestException as ex:
            raise ModuleRuntimeException("Unable to reach ViewDNS API: %s" % ex)

        # =====================================================================================
        # Process Response
        # =====================================================================================
        if response.status_code != 200:
            raise ModuleRuntimeException("Unexpected response from API: %s" % response.status_code)

        data = response.json()["response"]
        if "error" in data:
            raise ModuleRuntimeException("API Error: %s" % data["error"])

        account_info = response.json()["response"]
        self.debug("Fetch Account Balance: %s" % account_info)
        return account_info


