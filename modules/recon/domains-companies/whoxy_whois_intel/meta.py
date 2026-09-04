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
    name="Whoxy Whois Intel",
    authors=[
        'xvzf_opt (@xvzf_opt)'
    ],
    required_keys=["whoxy_api"],
    version="1.0.0",
    description="Uses the Whoxy API to query whois information for a domain, harvesting company and contact information",
    query="SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL",
    options=[
        ModuleOption(
            name="Confirm",
            default=True,
            required=True,
            description="Whether confirmation is required to proceed with the Whoxy API Query",
            validators=[validators.BooleanValidator()]
        )
    ],
    dependencies=[]
)

