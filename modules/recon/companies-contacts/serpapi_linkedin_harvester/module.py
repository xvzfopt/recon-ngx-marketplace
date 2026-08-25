# =====================================================================================
# Imports: External
# =====================================================================================
import os
import json
import serpapi
import html
from urllib.parse import unquote
from serpapi import Client
from recon.sdk import BaseModule
from recon.sdk import utils
from recon.sdk.exceptions import ModuleValidationException
from recon.sdk.exceptions import ModuleRuntimeException

# =====================================================================================
# Imports: Module Package
# =====================================================================================
from . import engines
from .mock_results import MockResults

# =====================================================================================
# Module Class: Shodan Hostname Enumerator
# =====================================================================================
class Module(BaseModule):
    '''
    Shodan Hostname Enumerator
    '''

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

        # Process Options
        self._page_limit            = self.get_option_value("PageLimit")
        self.__engine               = self.get_option_value("Engine")
        self._confirm_before_query  = self.get_option_value("Confirm")

        # Process Keys
        self._api_key = self.get_key("serpapi_api")

        # Set up Serp Client
        self._serpapi = Client(api_key=self._api_key)

        # =====================================================================================
        # Verify API Account
        # =====================================================================================
        try:
            self._account_info = self._serpapi.account()
            self.debug("SerpApi Account Info: %s" % self._account_info)
        except serpapi.HTTPError as ex:
            if ex.status_code == 401:
                raise ModuleValidationException("The configured SerpApi API key is invalid")
            raise

        # Check Account Status
        if self.get_total_remaining_searches() <= 0:
            raise ModuleValidationException("This account has ran out of searches for the current billing period.")
        elif self.get_hour_remaining_searches() <= 0:
            raise ModuleValidationException("This account has reached the hourly search limit. Please try again later")

    def module_run(self, companies):
        '''
        Override: Module execution
        '''
        self.debug(f"Selected Engine: {self.__engine}")

        # =====================================================================================
        # Check/Confirm API Usage
        # =====================================================================================
        # Check Search Limits
        proceed = "y"
        if len(companies) > self.get_hour_remaining_searches():
            proceed = self.read(
                f"The number of searches ({len(companies)}) will exceed your hourly search limit"
                f" ({self.get_hour_remaining_searches()}). Do you want to proceed? [y/N]: ", default="n"
            )
        elif len(companies) > self.get_total_remaining_searches():
            proceed = self.read(
                f"The number of searches ({len(companies)}) will exceed your available credits"
                f" ({self.get_total_remaining_searches()}). Do you want to proceed? [y/N]: ", default="n"
            )
        if proceed.lower() != "y":
            return

        # Get credit use authorisation
        proceed = "y"
        if self._confirm_before_query:
            credits_to_use = len(companies)
            proceed = self.read(
                "Proceed with query? (%s search credit(s) will be used) [y/N]: " % credits_to_use, default="n"
            )
        if proceed.lower() != "y":
            return

        # =====================================================================================
        # Iterate Target Companies
        # =====================================================================================
        count = 0
        profiles_created = 0
        contacts_created = 0

        with self.get_progress_bar(len(companies), unit="queries") as progress:
            for company in companies:
                progress.write(f"Target ({count + 1} of {len(companies)}): {company}")

                # =====================================================================================
                # Page Lookups
                # =====================================================================================
                page_no = 1
                results = None
                while True:

                    try:
                        # [Unit Test]: Read results from file
                        if self._test_results_file and os.path.isfile(self._test_results_file):
                            with open(self._test_results_file, "r") as results_file:
                                results = MockResults(json.load(results_file))
                        else:
                            if not results:
                                results = self._serpapi.search(self.build_query(self.__engine, company))
                            else:
                                results = results.next_page()

                        progress.update()

                    # =====================================================================================
                    # Exception Handler: HTTP Error
                    # =====================================================================================
                    except serpapi.HTTPError as ex:
                        self.debug("Error: (%s): %s" % (ex.status_code, ex.response.text))
                        if ex.status_code == 401:
                            raise ModuleRuntimeException("SerpApi API key is invalid")
                        elif ex.status_code == 429:
                            raise ModuleRuntimeException("SerpApi limits exceeded. Please check account status ")
                        raise

                    # =====================================================================================
                    # Process Results
                    # =====================================================================================
                    if "organic_results" not in results:
                        self.debug("No results found")
                        break

                    for result in results["organic_results"]:
                        contact_created, profile_created = self.process_search_result(company, result)
                        if contact_created:
                            contacts_created += 1
                        if profile_created:
                            profiles_created += 1
                        count += 1

                    # =====================================================================================
                    # Prepare for Next Page
                    # =====================================================================================
                    self.debug(f"Processed page: {page_no}")
                    # Check Page Limit
                    if page_no >= self._page_limit:
                        self.debug(f"Page Limit reached: {self._page_limit}")
                        break
                    # Check for more pages
                    if "serpapi_pagination" not in results:
                        self.debug("No more results.")
                        break
                    page_no += 1


        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Contacts created: %s" % contacts_created)
        self.output("Profiles created: %s" % profiles_created)

        # =====================================================================================
        # Print API Account Data
        # =====================================================================================
        self._account_info = self._serpapi.account()
        self.heading("SerpAPI Status", level=0)
        self.output("Total Searches Remaining: %s" % self.get_total_remaining_searches())
        self.output("Hourly Searches Remaining: %s" % self.get_hour_remaining_searches())

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def process_search_result(self, company, result):
        '''
        Process a search engine result, creating a contact and profile if possible

        :param company: The target company being investigated
        :type company: str
        :param result: The result to process
        :type result: dict
        :returns: Whether a contact, and profile, was created
        :rtype: tuple
        '''

        # Sanitise and Clean title
        title = result["title"]
        title = utils.clean_unicode_characters(title)
        title = html.unescape(title)

        # Clean URL
        link = unquote(result["link"])

        # =====================================================================================
        # Process Name
        # =====================================================================================
        fullname = title.split(" -")[0]     # Split on job title
        fullname = fullname.split(",")[0]   # Split on personal titles
        f_name, m_name, l_name = utils.parse_fullname(fullname)

        # =====================================================================================
        # Process Username and Job Title
        # =====================================================================================
        username = self.extract_username(link)
        job_title = self.extract_jobtitle(company, title)

        # =====================================================================================
        # Created Contact and Profile
        # =====================================================================================
        contact_created = self.insert_contacts(f_name, m_name, l_name, title=job_title)
        profile_created = self.insert_profiles(username, "LinkedIn", link, "social")

        return contact_created, profile_created

    def extract_username(self, url):
        '''
        Extracts a LinkedIn username from a URL

        :param url: The LinkedIn URL to extract the username from
        :type url: str
        :returns: The extracted username, or None if the username could not be extracted
        :rtype:str
        '''
        return url.split("/")[-1]

    def extract_jobtitle(self, company, result_title):
        '''
        Tries to extract a person's Job Title from a search engine result title

        :param company: The name of the company that is being investigated
        :type company: str
        :param result_title: The search engine result title
        :type result_title: str
        :returns: The extracted person's Job Title, or "Undetermined" if extraction was unsuccessful
        :rtype: str
        '''
        job_title = "Undetermined"

        # Check for truncation
        components = result_title.split(" - ")
        if len(components) == 2:
            # Make sure Job title is likely present
            if "@" in result_title or " at " in result_title:

                # Further processing
                snippet = components[1]                 # Ignore Full name
                snippet = snippet.split(" @ ")[0]       # Ignore Company
                snippet = snippet.split(" at ")[0]      # Ignore Company
                snippet = snippet.split(" | ")[0]       # Ignore LinkedIn

                job_title = snippet

        return job_title

    def build_query(self, engine, company):
        '''
        Builds the query for the specified Engine and Company

        :param engine: The search engine being used
        :type engine: str
        :param company: The target company
        :type company: str
        '''
        query = {"engine": engine}

        if engine in [engines.GOOGLE, engines.BAIDU, engines.DUCKDUCKGO]:
            query["q"] = f'site:linkedin.com/in/ "{company}"'
        elif engine in [engines.YAHOO]:
            query["p"] = f'site:linkedin.com/in/ "{company}"'
        elif engine in [engines.YANDEX]:
            query["text"] = f'site:linkedin.com/in/ "{company}"'

        return query

    def get_total_remaining_searches(self):
        '''
        Gets the number of searches that the account has left to use

        :returns: The total number of searches that the account has available to use
        :rtype: int
        '''
        return self._account_info.get("total_searches_left", 0)

    def get_hour_remaining_searches(self):
        '''
        Gets the number of searches that the account has left to use in the next hour

        :returns: The total number of searches that the account has available to use within the next hour period
        :rtype: int
        '''
        hour_search_limit = self._account_info.get("account_rate_limit_per_hour", 0)
        searches_in_last_hour = self._account_info.get("last_hour_searches", 0)
        return hour_search_limit - searches_in_last_hour
