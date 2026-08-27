# =====================================================================================
# Imports: External
# =====================================================================================
import time
import json
from shodan import Shodan
from shodan.exception import APIError
from recon.sdk import utils
from recon.sdk import BaseModule
from recon.sdk.exceptions import ModuleValidationException

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: Shodan IP Enumerator
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

    def module_run(self, ipaddrs):
        '''
        Override: Module execution
        '''

        # =====================================================================================
        # Check/Confirm API Usage
        # =====================================================================================
        proceed = "y"
        if self._confirm_before_query:
            credits_to_use = len(ipaddrs)
            proceed = self.read(
                "Proceed with query? (%s Shodan credit(s) will be used) [y/N]: " % credits_to_use, default="n"
            )
        if proceed.lower() != "y":
            return

        # =====================================================================================
        # Iterate Target IPs
        # =====================================================================================
        count = 1
        ports_discovered = 0
        vulns_discovered = 0

        with self.get_progress_bar(len(ipaddrs), unit="queries") as progress:
            for ipaddr in ipaddrs:
                progress.write(f"Target ({count} of {len(ipaddrs)}): {ipaddr}")

                # =====================================================================================
                # Fetch Host info
                # =====================================================================================
                try:
                    if self._test_results_file:
                        with open(self._test_results_file, "r") as results_file:
                            host_info = json.load(results_file)
                    else:
                        host_info = self._shodan.host(ipaddr)
                        time.sleep(1)  # Throttle
                except APIError as ex:
                    self.error("Encountered a fatal API Error: %s" % ex)
                    break

                progress.update()

                # =====================================================================================
                # Process Host Services
                # =====================================================================================
                for service in host_info.get("data"):

                    # =====================================================================================
                    # Process Port Data
                    # =====================================================================================
                    # Process Protocol
                    protocol = utils.shodan_identify_protocol(service)

                    # Process Port Data
                    port_data = {
                        "host": service.get("hostname", [""])[0],
                        "ip_address": ipaddr,
                        "port": service.get("port"),
                        "protocol": protocol
                    }
                    self.insert_ports(**port_data)

                    # Process Vulnerabilities
                    if "vulns" in service:
                        for service_vuln, service_vuln_data in service["vulns"].items():
                            vuln_data = {
                                "host": service_vuln_data.get("hostname", [ipaddr])[0],
                                "reference": service_vuln,
                                "status": "Verified" if service_vuln_data.get("verified", False) else "Unverified",
                                "cvss": service_vuln_data.get("cvss"),
                                "notes": f"Port: {service.get("port")}"
                            }
                            self.insert_vulnerabilities(**vuln_data)
                            vulns_discovered += 1

                    ports_discovered += 1

        # =====================================================================================
        # Print Summary
        # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Ports discovered: %s" % ports_discovered)
        self.output("Vulnerabilities discovered: %s" % ports_discovered)

        # =====================================================================================
        # Print API Account Data
        # =====================================================================================
        self._info = self._shodan.info()
        time.sleep(1) # Throttle
        self.heading("Shodan API Status", level=0)
        self.output("Query Credits Remaining: %s" % self._info.get("query_credits"))
        self.output("Scan Credits Remaining: %s" % self._info.get("scan_credits"))
