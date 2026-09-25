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
    name="GitHub Repo Discovery",
    authors=[
        'xvzf_opt (@xvzf_opt)'
],
    required_keys=["github_api"],
    version="1.0.0",
    description="Uses the GitHub API to enumerate a user's repositories and gists. Updates the 'repositories' "
                "table with the results",
    query="SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL and resource LIKE 'GitHub'",
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

