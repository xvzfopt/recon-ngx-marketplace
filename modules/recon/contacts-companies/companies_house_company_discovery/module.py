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
# Module Class: Companies House - Company Discovery
# =====================================================================================
class Module(BaseModule):
    '''
    Companies House - Companies Discovery
    '''

    # =====================================================================================
    # Module Properties
    # =====================================================================================
    BASE_URL = "https://api.company-information.service.gov.uk"

    EP_SEARCH           = "/search"
    EP_SEARCH_COMPANIES = EP_SEARCH + "/companies"
    EP_SEARCH_OFFICERS  = EP_SEARCH + "/officers"

    EP_COMPANY          = "/company"
    EP_OFFICERS         = "/officers"

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def preflight(self):
        '''
        Override: Module prelight
        '''
        self._headers = None
        self._test_results_file_officers                = None # Used for Test Cases
        self._test_results_file_officer_appointments    = None # Used for Test Cases
        self._test_results_file_company_data            = None # Used for Test Cases
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

    def module_run(self, officers):
        '''
        Override: Module execution
        '''
        count                   = 0
        officers_processed      = 0
        appointments_processed  = 0
        found_company_names     = []
        table_rows              = []

        # =====================================================================================
        # Iterate Officers
        # =====================================================================================
        for officer in officers:

            officer_search_results = self.search_officers(officer)
            with self.get_progress_bar(
                    len(officer_search_results),
                    description="Processing Search Results",
                    unit="results"
            ) as pb_search_results:
                for result in officer_search_results:
                    officer_id = result["links"]["self"].split("/")[2]
                    appointments = self.get_officer_appointments(officer_id)

                    # =====================================================================================
                    # Iterate Appointments
                    # =====================================================================================
                    for appointment in appointments:
                        # Process company of each appointment
                        company_number = appointment["appointed_to"]["company_number"]
                        company = self.get_company(company_number)
                        company_name = company["company_name"]

                        # Record discovery
                        if company_name not in found_company_names:
                            found_company_names.append(company_name)
                            table_rows.append([officer, company_name])

                        # Add company to Database
                        company_data = {"company": company_name}
                        self.insert_companies(**company_data, mute=True)
                        appointments_processed += 1

                    officers_processed += 1
                    pb_search_results.update()

            count += 1

        # =====================================================================================
        # Print Summary
        # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Officers Processed:\t\t%s" % officers_processed)
        self.output("Appointments Processed:\t%s" % officers_processed)
        self.output("Companies Processed:\t%s" % len(found_company_names))

        # Display Officer->Company table
        self.heading("Discovered companies")
        self.table(table_rows, ["Officer", "Company"])

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
    def search_officers(self, query):
        '''
        Performs an officers search and returns the results

        :param query: The query string
        :type query: str
        :returns: List of matching officers
        :rtype: list
        '''
        officers = []

        # Build URL
        url = f"{self.BASE_URL}{self.EP_SEARCH_OFFICERS}?q={parse.quote_plus(query)}&items_per_page={self._result_limit}"

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
                raise ModuleRuntimeException("Unexpected response from Companies House API: %s" % response.status_code)

        # =====================================================================================
        # Process Results
        # =====================================================================================
        for item in results["items"]:
            # Check result limit (Test purposes - API should enforce this)
            if len(officers) >= self._result_limit:
                self.debug("Officer limit reached. Breaking")
                break

            # Check for exact match
            if self._exact_match:
                self.debug(f"Performing exact match check: {item['title'].lower()} == {query.lower()}")
                if item["title"].lower() != query.lower():
                    continue
            officers.append(item)

        return officers

    def get_officer_appointments(self, officer_id):
        '''
        Gets a list of company appointments for the specified officer

        :param officer_id: The ID of the target officer
        :type officer_id: str
        '''
        appointments = []

        # Build URL
        url = f"{self.BASE_URL}{self.EP_OFFICERS}/{officer_id}/appointments"

        # =====================================================================================
        # Send Request
        # =====================================================================================
        if self._test_results_file_officer_appointments:
            with open(self._test_results_file_officer_appointments, "r") as results_file:
                results = json.load(results_file)
        else:
            try:
                response = self.request("GET", url, headers=self.get_headers())
                results = response.json()
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
        # Process Data
        # =====================================================================================
        for item in results["items"]:
            appointments.append(item)

        return appointments

    def get_company(self, company_number):
        '''
        Gets the data for a specified company

        :param company_number: The target company's company number
        :type company_number: str
        '''
        company_data = {}

        # Build URL
        url = f"{self.BASE_URL}{self.EP_COMPANY}/{company_number}"

        # =====================================================================================
        # Send Request
        # =====================================================================================
        if self._test_results_file_company_data:
            with open(self._test_results_file_company_data, "r") as results_file:
                company_data = json.load(results_file)
        else:
            try:
                response = self.request("GET", url, headers=self.get_headers())
                company_data = response.json()
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

        return company_data

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
