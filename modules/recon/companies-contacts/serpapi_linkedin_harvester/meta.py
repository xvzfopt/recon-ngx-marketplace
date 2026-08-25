# =====================================================================================
# Imports: External
# =====================================================================================
from recon.sdk import ModuleMetadata
from recon.sdk import ModuleOption
from recon.sdk import validators

# =====================================================================================
# Imports: Internal
# =====================================================================================
from . import engines

# =====================================================================================
# Module Metadata
# =====================================================================================
meta = ModuleMetadata(
    name="SerpApi LinkedIn Harvester",
    authors=[
        'xvzf_opt (@xvzf_opt)'
    ],
    version="1.1.0",
    description="Harvests profiles from LinkedIn related to the given company by using SerpApi to search across various"
                " Search Engines. Profiles are added to the 'profiles' table, while contact information is added to "
                " the 'contacts' table."
                " This module does not access LinkedIn at any time, but does require a SerpApi key",
    required_keys=["serpapi_api"],
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
            name="Engine",
            default="google",
            required=True,
            description=f"The target search engine to run the query across. Options: {', '.join(engines.SUPPORTED_ENGINES)}",
            validators=[validators.ChoicesValidator(engines.SUPPORTED_ENGINES)]
        ),
        ModuleOption(
            name="Confirm",
            default=True,
            required=True,
            description="Whether confirmation is required to proceed with the SerpApi Query",
            validators=[validators.BooleanValidator()]
        )
    ],
    dependencies=["serpapi"]
)

