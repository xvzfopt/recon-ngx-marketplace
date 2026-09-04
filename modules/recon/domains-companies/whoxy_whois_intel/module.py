# =====================================================================================

# Imports: External
# =====================================================================================
import json
import os.path
from urllib.parse import quote

import requests.exceptions
from pytz import country_names

from recon.sdk import BaseModule
from recon.sdk import utils
from recon.sdk.exceptions import ModuleRuntimeException
from recon.sdk.exceptions import ModuleValidationException
from requests.exceptions import RequestException

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: Whoxy Whois Intel
# =====================================================================================
class Module(BaseModule):
    '''
    Whoxy Whois Intel Module
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
        self._confirm_before_run = self.get_option_value("Confirm")

        # Process Keys
        self._api_key = self.keys.get("whoxy_api")

        # =====================================================================================
        # Check Account Balance
        # =====================================================================================
        if self.get_credits_remaining() <= 0:
            raise ModuleValidationException(
                "No Whois Lookup credits on this account. Please add credits to use this module"
            )

    def module_run(self, domains):
        '''
        Override: Module execution
        '''
        count = 0
        total_contacts_created = 0
        total_companies_created = 0

        # =====================================================================================
        # Check for sufficient credits
        # =====================================================================================
        if self.get_credits_remaining() < len(domains):
            raise ModuleValidationException(
                f"Query requires {len(domains)} credit(s), but there are only {self.get_credits_remaining()} available."
                f" Please add more credits to continue"
            )

        # =====================================================================================
        # Check/Confirm API Usage
        # =====================================================================================
        proceed = "y"
        if self._confirm_before_run:
            credits_to_use = len(domains)
            proceed = self.read(
                "Proceed with query? (%s Whoxy credit(s) will be used) [y/N]: " % credits_to_use, default="n"
            )
        if proceed.lower() != "y":
            return

        # =====================================================================================
        # Iterate Companies
        # =====================================================================================
        with self.get_progress_bar(len(domains), unit="queries") as progress:
            for domain in domains:
                progress.write(f"Target ({count + 1} of {len(domains)}): {domain}")

                # =====================================================================================
                # Send Request
                # =====================================================================================
                if not self._test_results_file or not os.path.isfile(self._test_results_file):
                    try:
                        url = f"{self.BASE_URL}/?key={self._api_key}&whois={domain}"
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
                contacts_created, companies_created = self.process_record(data)
                total_contacts_created += contacts_created
                total_companies_created += companies_created

                count += 1
                progress.update()

        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Contacts created: %s" % total_contacts_created)
        self.output("Companies created: %s" % total_companies_created)

        # =====================================================================================
        # Print API Account Data
        # =====================================================================================
        self._account_balance = self.fetch_account_balance()
        self.heading("Whoxy API Status", level=0)
        self.output("Credits Remaining: %s" % self.get_credits_remaining())

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def process_record(self, record):
        '''
        Processes a Whois record

        :param record: The whois record to process
        :type record: dict
        '''
        contacts_created = 0
        companies_created = 0

        # Extract contact data
        registrant_contact      = record.get("registrant_contact")
        administrative_contact  = record.get("administrative_contact")
        technical_contact       = record.get("technical_contact")

        # =====================================================================================
        # Process Contacts
        # =====================================================================================
        for contact in [registrant_contact, administrative_contact, technical_contact]:
            if not contact:
                continue

            # Process Name
            full_name       = self.filter_redaction(contact.get("full_name"))
            f_name, m_name, l_name = utils.parse_fullname(full_name)

            # Process Email
            email = self.filter_redaction(contact.get("email_address"))
            if not email or "@" not in email:
                continue

            # Add Contact
            contact_data = {
                "first_name": f_name,
                "middle_name": m_name,
                "last_name": l_name,
                "email": email,
                "region": self.filter_redaction(contact.get("state_name")),
                "country": self.filter_redaction(contact.get("country_name")),
                "city": self.filter_redaction(contact.get("city_name")),
                "phone": self.filter_redaction(contact.get("phone_number"))
            }
            contacts_created += self.insert_contacts(**contact_data)

            # Add Company
            company_name = self.filter_redaction(contact.get("company_name"))
            if company_name:
                companies_created += self.insert_companies(company=company_name)

        return contacts_created, companies_created

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
        remaining = self._account_balance.get("live_whois_balance", 0)

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

    def filter_redaction(self, value):
        '''
        Checks if the specified whois field value has been redacted for privacy

        :param value: The value to check
        :type value: str
        :returns: True if redacted, otherwise False
        :rtype: bool
        '''
        filtered_value = None
        if value and "redacted" not in value.lower() and "privacy" not in value.lower():
            filtered_value = value
        return filtered_value



