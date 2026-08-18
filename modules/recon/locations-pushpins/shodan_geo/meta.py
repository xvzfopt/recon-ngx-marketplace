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
    name="Shodan Geolocation Search",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        "Tim Tomes (@lanmaster53)",
        "Ryan Hays (@_ryanhays)"
    ],
    version="2.0.0",
    description="Searches Shodan for devices within the specified proximity of a location",
    required_keys=["shodan_api"],
    comments=[
        "Shodan \'geo\' searches can take a long time to complete. If receiving timeout errors, increase the "
        "global TIMEOUT option"
    ],
    query="SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND "
          "longitude IS NOT NULL",
    options=[
        ModuleOption(
            name="PageLimit",
            default=1,
            required=True,
            description="Limit the number of pages of results that will be processed for each lookup",
            validators=[validators.IntegerValidator]
        ),
        ModuleOption(
            name="Radius",
            default=1,
            required=True,
            description="Radius in Kilometers to search around the target location(s)",
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

