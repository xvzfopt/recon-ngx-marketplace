# =====================================================================================
# Imports: External
# =====================================================================================
from recon.sdk import ModuleMetadata
from recon.sdk import ModuleOption
from recon.sdk import validators

# =====================================================================================
# Imports: Internal
# =====================================================================================

# =====================================================================================
# Module Metadata
# =====================================================================================
meta = ModuleMetadata(
    name="ViewDNS Domains Finder",
    authors=[
        'xvzf_opt (@xvzf_opt)'
    ],
    required_keys=["viewdns_api"],
    version="1.0.0",
    description="Finds Domain Names associated with, or belonging to, a particular company by using the viewdns.info"
                " Reverse Whois Lookup tool",
    query="SELECT DISTINCT company FROM companies WHERE company IS NOT NULL",
    options=[],
    dependencies=[]
)

