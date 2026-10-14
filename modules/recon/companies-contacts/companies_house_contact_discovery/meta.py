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
    name="Companies House - Contact Discovery",
    authors=[
        'xvzf_opt (@xvzf_opt)',
    ],
    version="1.0.0",
    description="Finds officers listed for a company in the Companies House Register. Updates the 'contacts'"
                " table with the result",
    required_keys=["companies_house_api"],
    query="SELECT DISTINCT company FROM companies WHERE company IS NOT NULL",
    options=[
        ModuleOption(
            name="ExactMatch",
            required=True,
            default=True,
            description="Whether or not to require an exact match of the company name",
            validators=[validators.BooleanValidator()]
        ),
        ModuleOption(
            name="ResultLimit",
            default=10,
            required=False,
            description="Limits the number of results to process for a company search",
            validators=[validators.IntegerValidator()]
        )
    ],
    dependencies=[""]
)

