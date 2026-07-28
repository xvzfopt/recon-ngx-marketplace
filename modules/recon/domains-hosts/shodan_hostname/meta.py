# =====================================================================================
# Imports: External
# =====================================================================================
from recon.sdk import ModuleMetadata
from recon.sdk import ModuleOption

# =====================================================================================
# Module Metadata
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

