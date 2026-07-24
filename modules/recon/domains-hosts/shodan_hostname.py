# =====================================================================================
# Imports: External
# =====================================================================================
import shodan
import time
from recon.sdk import BaseModule
from recon.sdk import ModuleMetadata
from recon.sdk import ModuleOption

# =====================================================================================
# Module Class: Shodan Hostname Enumerator
# =====================================================================================
class Module(BaseModule):
    '''
    Shodan Hostname Enumerator
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    meta = ModuleMetadata(
        name="Shodan Hostname Enumerator",
        authors=[
            'xvzf_opt (@xvzf_opt)',
            "Tim Tomes (@lanmaster53)",
            "Ryan Hays (@_ryanhays)"
        ],
        version="2.0.1.rc0",
        description="Harvests hosts from the Shodan API by using the \'hostname\' search operator. Updates the "
                    "\'hosts\' table with the results.",
        required_keys=["shodan_api"],
        query="SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL",
        options=[
            ModuleOption(
                name="limit",
                default=1,
                required=True,
                description="Limit number of api requests per input source (0 = unlimited)"
            )
        ],
        dependencies=["shodan"]
    )

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

            except shodan.exception.APIError:
                pass
