# =====================================================================================
# Imports: External
# =====================================================================================
import time
import json
from datetime import datetime
from shodan import Shodan
from shodan.exception import APIError
from recon.sdk import BaseModule
from recon.sdk.exceptions import ModuleValidationException

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: Shodan Geolocation Search
# =====================================================================================
class Module(BaseModule):
    '''
    Shodan Geolocation Search Module
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
        self._confirm_before_query  = self.get_option_value("Confirm")
        self._search_radius         = self.get_option_value("Radius")

        # Process Keys
        self._api_key = self.get_key("shodan_api")

        # Set up Shodan
        self._shodan = Shodan(self._api_key)

        # =====================================================================================
        # Verify API Account
        # =====================================================================================
        try:
            self._account_info = self._shodan.info()
            time.sleep(1)  # Throttle
        except APIError as ex:
            if str(ex).lower().startswith("invalid api key"):
                raise ModuleValidationException("The configured Shodan API Key is invalid.")
            raise ModuleValidationException("Shodan API error encountered: %s" % ex)
        finally:
            time.sleep(1)  # Throttle

    def module_run(self, locations):
        '''
        Override: Module execution
        '''

        # =====================================================================================
        # Check/Confirm API Usage
        # =====================================================================================
        proceed = "y"
        if self._confirm_before_query:
            credits_to_use = len(locations)
            proceed = self.read(
                "Proceed with query? (%s Shodan credit(s) will be used) [y/N]: " % credits_to_use, default="n"
            )
        if proceed.lower() != "y":
            return

        # =====================================================================================
        # Iterate Target Domains
        # =====================================================================================
        count = 1
        pushpins_count = 0

        with self.get_progress_bar(len(locations), unit="queries") as progress:
            self.output(f"Search Radius: {self._search_radius} KM")
            for location in locations:
                page = 1
                query = f"geo:{location},{self._search_radius}"
                progress.write(f"Location ({count} of {len(locations)}): {location}")

                # =====================================================================================
                # Page Lookups
                # =====================================================================================
                while page <= self._page_limit:
                    self.debug("Fetching page: %s" % page)
                    try:
                        if self._test_results_file:
                            with open(self._test_results_file, "r") as results_file:
                                results = json.load(results_file)
                        else:
                            results = self._shodan.search(query, page=page)
                            time.sleep(1)  # Throttle
                    except APIError as ex:
                        self.error("Encountered a fatal API Error: %s" % ex)
                        break

                    # =====================================================================================
                    # Process Results
                    # =====================================================================================
                    for match in results["matches"]:
                        if len(match["hostnames"]) > 0:
                            for hostname in match["hostnames"]:
                                pushpin_data = self.build_pushpin_data(hostname, match)
                                self.insert_pushpins(**pushpin_data)
                                pushpins_count += 1
                        else:
                            pushpin_data = self.build_pushpin_data(match.get("ip_str", "None"), match)
                            self.insert_pushpins(**pushpin_data)
                            pushpins_count += 1

                    progress.update()
                    page += 1

        # =====================================================================================
        # Print Summary
        # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Pushpins identified: %s" % pushpins_count)

        # =====================================================================================
        # Print API Account Data
        # =====================================================================================
        self._info = self._shodan.info()
        time.sleep(1) # Throttle
        self.heading("Shodan API Status", level=0)
        self.output("Query Credits Remaining: %s" % self._info.get("query_credits"))
        self.output("Scan Credits Remaining: %s" % self._info.get("scan_credits"))


    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def build_pushpin_data(self, hostname, host_data):
        '''
        Builds pushpin data for the specified host
        Note: This has been ported directly from recon-ng, at least in the context of the data returned.
        We need to review this to see if it's actually of use. Some elements don't make a great deal of sense

        :param hostname: The host's hostname
        :type hostname: str
        :param host_data: The host's data from shodan
        :type host_data: dict
        :returns: Pushpin data dictionary
        :rtype: dict
        '''

        # Build Host Socket Address
        host_socket = f"{host_data['ip_str']}:{host_data['port']}"

        # Build Message
        message = (
            f"Hostname: {hostname} | City: {host_data['location']['city']} | State: {host_data['location']['region_code']} "
            f"| Country: {host_data['location']['country_name']} | OS: {host_data["os"]}"
        )

        # Build Pushpin Data
        pushpin_data = {
            "source": "Shodan",
            "screen_name":  host_socket,
            "profile_name": host_socket,
            "profile_url": f"http://{host_socket}",
            "media_url": f"https://www.shodan.io/host/{host_data['ip_str']}",
            "thumb_url": "https://gravatar.com/avatar/ffc4048d63729d4932fd3cc45139174f?s=300",
            "message": message,
            "latitude": host_data["location"]["latitude"],
            "longitude": host_data["location"]["longitude"],
            "time": datetime.strptime(host_data['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
        }

        return pushpin_data
