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
    name="GitHub Company Miner",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        'Tim Tomes (@lanmaster53)',
],
    required_keys=["github_api"],
    version="2.0.0",
    description="Uses the GitHub API to enumerate repositories and member profiles associated with a company search string",
    query="SELECT DISTINCT company FROM companies WHERE company IS NOT NULL",
    options=[
        ModuleOption(
            name="IgnoreForks",
            default=True,
            required=True,
            description="Whether forked repositories should be ignored.",
            validators=[validators.BooleanValidator()]
        ),
        ModuleOption(
            name="PageLimit",
            default=1,
            required=True,
            description="Limit the number of pages of results that will be processed for each lookup",
            validators=[validators.IntegerValidator()]
        ),
    ],
    dependencies=[]
)

