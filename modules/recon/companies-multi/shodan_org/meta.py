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
    name="Shodan Organisation Enumerator",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        "Austin Tipton (@hiEntripy404)",
        "Ryan Hays (@_ryanhays)"
    ],
    version="2.1.0",
    description="Harvests host and port information from the Shodan API by using the \'org\' search operator. "
                "Updates the \'hosts\' and \'ports\' table with the results.",
    required_keys=["shodan_api"],
    query="SELECT DISTINCT company FROM companies WHERE company IS NOT NULL",
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

