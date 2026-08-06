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
    name="Shodan Network Enumerator",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        "Mike Siegel",
        "Tim Tomes (@lanmaster53)",
        "Ryan Hays (@_ryanhays)"
    ],
    version="2.0.0",
    description="Harvests hosts from the Shodan API by using the \'net\' search operator. Updates the "
                "\'hosts\' table with the results.",
    required_keys=["shodan_api"],
    query="SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL",
    options=[
        ModuleOption(
            name="PageLimit",
            default=1,
            required=True,
            description="Limit the number of pages of results that will be processed for each lookup",
            validators=[validators.IntegerValidator]
        ),
        ModuleOption(
            name="Confirm",
            default=True,
            required=True,
            description="Whether confirmation is required to proceed with the Shodan API Query",
            validators=[validators.BooleanValidator]
        )
    ],
    dependencies=["shodan"]
)

