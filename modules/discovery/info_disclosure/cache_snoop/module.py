# =====================================================================================
# Imports: External
# =====================================================================================
import os
import dns.message
import dns.query
from recon.sdk import BaseModule
from recon.sdk import ModuleMetadata
from recon.sdk import ModuleOption
from recon.sdk import validators
from recon.sdk.exceptions import *

# =====================================================================================
# Modules Class: DNS Cache Snooper
# =====================================================================================
class Module(BaseModule):
    '''
    DNS Cache Snooper
    '''

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def module_pre(self):
        '''
        Override: Set up module properties and perform additional validation
        '''

        # Process Options
        self._nameserver = self.get_option_value('nameserver')

        # Resolve Domains File Path
        self._domains_file = self.get_option_value('domains')
        if not os.path.isfile(self._domains_file):
            self._domains_file = os.path.join(self.get_package_path(), self.get_option_value("domains"))

    def module_run(self):
        '''
        Module run function
        '''

        # Read Domain Names from file
        with open(self._domains_file, "r") as fp:
            domains = [x.strip() for x in fp.read().split()]

        # Iterate Domain names and Query Nameserver
        for domain in domains:
            response = None

            # =====================================================================================
            # Prepare DNS Query
            # =====================================================================================
            query = dns.message.make_query(domain, dns.rdatatype.A, dns.rdataclass.IN)
            # unset the Recurse flag
            query.flags ^= dns.flags.RD

            # =====================================================================================
            # Attempt Query
            # =====================================================================================
            try:
                response = dns.query.udp(query, self._nameserver)
            except PermissionError:
                self.error(
                    "Permission error encountered while querying nameserver. Are you behind TOR or a VPN?"
                    " if so, your networking may be configured to block outbound DNS requests."
                )
                return

            # =====================================================================================
            # Process Response
            # =====================================================================================
            if len(response.answer) > 0:
                self.alert(f"{domain} => Snooped!")
            else:
                self.verbose(f"{domain} => Not Found.")

        self.output("Execution complete. %s Domain Name(s) checked." % len(domains))
