# =====================================================================================
# Imports: External
# =====================================================================================
import json
from urllib import parse
from recon.sdk import utils
from recon.sdk import BaseModule
from recon.sdk.exceptions import ModuleRuntimeException
from recon.sdk.exceptions import ModuleValidationException
from requests.exceptions import RequestException
from requests.exceptions import JSONDecodeError

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: Companies House - Contact Discovery
# =====================================================================================
class Module(BaseModule):
    '''
    Companies House - Contact Discovery
    '''

    # =====================================================================================
    # Module Properties
    # =====================================================================================
    BASE_URL = "https://api.company-information.service.gov.uk"

    EP_SEARCH           = "/search"
    EP_SEARCH_COMPANIES = EP_SEARCH + "/companies"
    EP_SEARCH_OFFICERS  = EP_SEARCH + "/officers"

    EP_COMPANY          = "/company"

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def preflight(self):
        '''
        Override: Module prelight
        '''
        self._headers = None
        self._test_results_file_companies   = None # Used for Test Cases
        self._test_results_file_officers    = None # Used for Test Cases
        return super().preflight()

    def module_pre(self):
        '''
        Override: Set up module properties and perform any additional validation
        '''

        # Process Options
        self._exact_match       = self.get_option_value("ExactMatch")
        self._result_limit      = self.get_option_value("ResultLimit")

        # Process Keys
        self._api_key = self.get_key("companies_house_api")

    def module_run(self, companies):
        '''
        Override: Module execution
        '''
        contacts_created = 0
        contacts_skipped = 0
        company_numbers = {}

        # =====================================================================================
        # Search Companies
        # =====================================================================================
        self.output("Searching for company information...")
        for company in companies:
            for result in self.search_companies(company):
                company_numbers[result["company_number"]] = result["title"]

        # =====================================================================================
        # Enumerate Company Officers
        # =====================================================================================
        count = 0
        self.output("Enumerating company officers...")
        with self.get_progress_bar(len(company_numbers), unit="results") as progress:
            for company_number in company_numbers:
                company = company_numbers[company_number]
                progress.write(f"Company ({count + 1} of {len(company_numbers)}): {company}")

                self.debug("Getting officers for company: %s" % company_number)
                officers = self.get_company_officers(company_number)
                for officer in officers:
                    f_name, m_name, l_name = self.process_officer_name(officer["name"])
                    officer_data = {
                        "first_name": f_name,
                        "middle_name": m_name,
                        "last_name": l_name,
                        "title": officer["officer_role"],
                        "region": officer["address"].get("region", "").strip(", "),
                        "country": officer["address"].get("country", "").strip(", "),
                        "city": officer["address"].get("locality", "").strip(", "),
                    }
                    creations = self.insert_contacts(**officer_data)
                    if creations:
                        contacts_created += creations
                    else:
                        contacts_skipped += 1

                count += 1
                progress.update()

        # =====================================================================================
        # Print Summary
        # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Contacts Created:\t%s" % contacts_created)
        self.output("Contacts Skipped:\t%s" % contacts_skipped)

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
    def process_officer_name(self, name):
        '''
        Parses and processes the name of a company officer, returning their first, middle and last name if possible

        :param name: The officer's "name" entry
        :type name: str
        '''
        f_name = None
        m_name = None
        l_name = None

        if "," in name:
            components = name.split(",")
            l_name = components[0].capitalize()
            remainder = ",".join(components[1:]).strip()

            if " " in remainder:
                f_name = remainder.split(" ")[0].capitalize()
                m_name = " ".join(remainder.split(" ")[1:]).capitalize()
            else:
                f_name = remainder.capitalize()
        else:
            f_name = name.capitalize()

        return f_name, m_name, l_name

    def search_companies(self, company):
        '''
        Performs a companies search and returns the results

        :param query: The query string
        :type query: str
        :returns: List of matching companies
        :rtype: list
        '''
        companies = []

        # Build URL
        url = f"{self.BASE_URL}{self.EP_SEARCH_COMPANIES}?q={parse.quote_plus(company)}&items_per_page={self._result_limit}"

        # =====================================================================================
        # Send Request
        # =====================================================================================
        if self._test_results_file_companies:
            with open(self._test_results_file_companies, "r") as results_file:
                results = json.load(results_file)
        else:
            try:
                response = self.request("GET", url, headers=self.get_headers())
                results = json.loads(response.text)
            except JSONDecodeError as ex:
                self.debug("Bad API response: %s" % response.text)
                raise ModuleValidationException("Unexpected response from Companies House API. Please check debug output")
            except RequestException as ex:
                raise ModuleRuntimeException("Unable to reach Companies House API: %s" % ex)

            # Check Response
            if response.status_code == 401:
                raise ModuleValidationException("Invalid authentication key. Please check key and try again")
            elif response.status_code != 200:
                raise ModuleRuntimeException("Unexpected response from Companies House API: %s" % response.status_code)

        # =====================================================================================
        # Process Results
        # =====================================================================================
        for item in results["items"]:
            # Check Result limit (manual break for test purposes)
            if len(companies) >= self._result_limit:
                break
            # Check for match
            if self._exact_match:
                self.debug("Performing exact match check: %s == %s" % (item["title"].lower(), company.lower()))
                if item["title"].lower() != company.lower():
                    continue
            companies.append(item)

        return companies

    def get_company_officers(self, company_number):
        '''
        Gets a list of officers for the specified company

        :param company_number: The company number of the target company
        :type company_number: str
        '''
        officers = []

        # Build URL
        url = f"{self.BASE_URL}{self.EP_COMPANY}/{company_number}/officers"

        # =====================================================================================
        # Send Request
        # =====================================================================================
        if self._test_results_file_officers:
            with open(self._test_results_file_officers, "r") as results_file:
                results = json.load(results_file)
        else:
            try:
                response = self.request("GET", url, headers=self.get_headers())
                results = json.loads(response.text)
            except JSONDecodeError as ex:
                self.debug("Bad API response: %s" % response.text)
                raise ModuleValidationException("Unexpected response from Companies House API. Please check debug output")
            except RequestException as ex:
              raise ModuleRuntimeException("Unable to reach Companies House API: %s" % ex)

            # Check Response
            if response.status_code == 401:
                raise ModuleValidationException("Invalid authentication key. Please check key and try again")
            elif response.status_code != 200:
                raise ModuleRuntimeException("Unexpected response from API: %s" % response.status_code)

        # =====================================================================================
        # Process Data
        # =====================================================================================
        for item in results["items"]:
            officers.append(item)

        return officers

    def get_headers(self):
        '''
        Builds and returns the Company House API headers

        :returns: The GitHub API headers
        :rtype: dict
        '''

        if not self._headers:
            self._headers = {
                "Authorization": "Basic " + utils.create_basic_auth_token(self._api_key, "")
            }
        return self._headers
