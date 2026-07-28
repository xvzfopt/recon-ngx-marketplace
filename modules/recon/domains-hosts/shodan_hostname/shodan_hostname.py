# =====================================================================================
# Imports: External
# =====================================================================================
import shodan
import time
from recon.sdk import BaseModule

# =====================================================================================
# Imports: Module Package
# =====================================================================================
from . import meta
from .exceptions import ShodanAuthFailure

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
    def module_run(self, domains):
        limit = self.get_option_value('limit')
        api = shodan.Shodan(self.get_key('shodan_api'))

        for domain in domains:
            self.heading(domain, level=0)
            query = f"hostname:{domain}"

            try:
                page = 1
                rec_count = 0
                total_results = 1
                while rec_count < total_results:
                    results = api.search(query, page=page)
                    print("results:" % results)
                    total_results = results['total']

                    for host in results['matches']:
                        rec_count += 1
                        try:
                            for hostname in host['hostnames']:
                                self.insert_ports(host=hostname, ip_address=host['ip_str'], port=host['port'],
                                                  protocol=host['transport'])
                                self.insert_hosts(host=hostname, ip_address=host['ip_str'])
                        except KeyError:
                            self.insert_ports(ip_address=ipaddr, port=host['port'], protocol=host['transport'])
                            self.insert_host(ip_address=host['ip_str'])

                    page += 1
                    time.sleep(limit)

            except shodan.exception.APIError as ex:
                print("API Error: %s: %s" % (ex, ex.value))
