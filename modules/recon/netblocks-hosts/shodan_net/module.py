# =====================================================================================
# Imports: External
# =====================================================================================
import time
import json
from shodan import Shodan
from shodan.exception import APIError
from recon.sdk import BaseModule
from recon.sdk.exceptions import ModuleValidationException

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: Shodan Network Enumerator
# =====================================================================================
class Module(BaseModule):
    '''
    Shodan Network Enumerator
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

    def module_run(self, netblocks):
        '''
        Override: Module execution
        '''

        # =====================================================================================
        # Check/Confirm API Usage
        # =====================================================================================
        proceed = "y"
        if self._confirm_before_query:
            credits_to_use = len(netblocks)
            proceed = self.read(
                "Proceed with query? (%s Shodan credit(s) will be used) [y/N]: " % credits_to_use, default="n"
            )
        if proceed.lower() != "y":
            return

        # =====================================================================================
        # Iterate Target Domains
        # =====================================================================================
        count = 1
        ports_discovered = 0
        hosts_discovered = 0

        with self.get_progress_bar(len(netblocks), unit="queries") as progress:
            for netblock in netblocks:
                page = 1
                query = f"net:{netblock}"
                progress.write(f"Target ({count} of {len(netblocks)}): {netblock}")

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

                    progress.update()
                    # =====================================================================================
                    # Process Match
                    # =====================================================================================
                    for match in results['matches']:
                        hosts_discovered += 1
                        for hostname in match['hostnames']:

                            # Process Host Data
                            host_data = {
                                "host": hostname,
                                "ip_address": match.get("ip_str"),
                                "region": match.get("location", {}).get("region_code"),
                                "city": match.get("location", {}).get("city"),
                                "country": match.get("location", {}).get("country_name"),
                                "latitude": match.get("location", {}).get("latitude"),
                                "longitude": match.get("location", {}).get("longitude"),
                            }
                            if match.get("org"):
                                host_data["notes"] = "Org: %s" % match.get("org")
                            self.insert_hosts(**host_data)

                            # Process Port Data
                            port_data = {
                                "host": hostname,
                                "ip_address": match.get("ip_str"),
                                "port":match.get("port"),
                                "protocol": match.get("transport")
                            }
                            self.insert_ports(**port_data)
                            ports_discovered += 1

                    page += 1

        # =====================================================================================
        # Print Summary
        # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Hosts discovered: %s" % hosts_discovered)
        self.output("Ports discovered: %s" % ports_discovered)

        # =====================================================================================
        # Print API Account Data
        # =====================================================================================
        self._info = self._shodan.info()
        time.sleep(1) # Throttle
        self.heading("Shodan API Status", level=0)
        self.output("Query Credits Remaining: %s" % self._info.get("query_credits"))
        self.output("Scan Credits Remaining: %s" % self._info.get("scan_credits"))
