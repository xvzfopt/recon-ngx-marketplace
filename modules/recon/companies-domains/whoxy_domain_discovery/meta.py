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
    name="Whoxy Domain Discovery",
    authors=[
        'xvzf_opt (@xvzf_opt)'
    ],
    required_keys=["whoxy_api"],
    version="1.0.0",
    description="Uses the Whoxy API to query for DNS records associated with a company",
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
            description="Whether confirmation is required to proceed with the Whoxy API Query",
            validators=[validators.BooleanValidator()]
        )
    ],
    dependencies=[]
)

