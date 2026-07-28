# =====================================================================================
# Imports: External
# =====================================================================================
from recon.sdk import ModuleMetadata
from recon.sdk import ModuleOption
from recon.sdk import validators

# =====================================================================================
# Module Metadata
# =====================================================================================
meta = ModuleMetadata(
    name="DNS Cache Snooper",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        'thrapt (thrapt@gmail.com)'
    ],
    description='Uses the DNS cache snooping technique to check for visited domains',
    version='3.0',
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
            default="data/av_domains.lst",
            required=True,
            description="File containing the list of domains to snoop for",
            validators=[validators.ValidFileValidator]
        )
    ]
)

