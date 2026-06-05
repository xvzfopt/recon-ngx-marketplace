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
    # Properties
    # =====================================================================================
    meta = ModuleMetadata(
        name="DNS Cache Snooper",
        authors=[
            'xvzf_opt (https://x.com/xvzf_opt)',
            'thrapt (thrapt@gmail.com)'
        ],
        description='Uses the DNS cache snooping technique to check for visited domains',
        version='2.0',
        comments=[
            'Nameserver must be in IP form.',
            'http://304geeks.blogspot.com/2013/01/dns-scraping-for-corporate-av-detection.html',
        ],
        options=[
            ModuleOption(
                name="nameserver",
                default="",
                required=True,
                description="IP address of authoritative nameserver",
                validators=[validators.Ipv4AddressValidator]
            ),
            ModuleOption(
                name="domains",
                default="av_domains.lst",
                required=True,
                description="File containing the list of domains to snoop for",
            )
        ],
        files=['av_domains.lst']
    )

    # =====================================================================================
    # Functions
    # =====================================================================================
    def module_pre(self):
        '''
        Override: Set up module properties and perform additional validation
        '''

        # Process Options
        self._nameserver = self.get_option_value('nameserver')
        self._domains_file = os.path.join(self.get_data_path(), self.get_option_value("domains"))

        # Check Domains file is valid
        if not os.path.isfile(self._domains_file):
            raise ModuleValidationException(
                "The specified domains file could not be found (%s). Check the file name in the 'domains'"
                " option is correct and try again."
                % self._domains_file
            )

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
