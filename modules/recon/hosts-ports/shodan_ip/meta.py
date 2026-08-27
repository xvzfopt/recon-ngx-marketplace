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
    name="Shodan IP Enumerator",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        "Tim Tomes (@lanmaster53)",
        "Matt Puckett (@t3lc0)"
        "Ryan Hays (@_ryanhays)"
    ],
    version="2.1.0",
    description="Harvests port and vulnerability information from the Shodan API by using the \'ip\' search operator. "
                "Updates the \'ports\' and \'vulnerabilites\' tables with the results.",
    required_keys=["shodan_api"],
    query="SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL",
    options=[
        ModuleOption(
            name="PageLimit",
            default=1,
            required=True,
            description="Limit the number of pages of results that will be processed for each lookup",
            validators=[validators.IntegerValidator()]
        ),
        ModuleOption(
            name="Confirm",
            default=True,
            required=True,
            description="Whether confirmation is required to proceed with the Shodan API Query",
            validators=[validators.BooleanValidator()]
        )
    ],
    dependencies=["shodan"]
)

