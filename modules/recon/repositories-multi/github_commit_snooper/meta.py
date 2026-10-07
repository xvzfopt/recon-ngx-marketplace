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
    name="GitHub Commit Snooper",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        'Michael Henriksen (@michenriksen)'
    ],
    required_keys=["github_api"],
    version="2.0.0",
    description="Uses the GitHub API to gather users from repository commits. Updates the 'profiles' and"
                " 'contacts 'tables with the results",
    query="SELECT DISTINCT owner, name FROM repositories WHERE resource LIKE 'GitHub' and category LIKE 'repo'",
    options=[
        ModuleOption(
            name="PageLimit",
            default=1,
            required=True,
            description="Maximum number of commit pages to process for each repository (0 = unlimited)",
            validators=[validators.IntegerValidator()]
        ),
        ModuleOption(
            name="ExtractAuthor",
            default=True,
            required=True,
            description="Whether to extract author information",
            validators=[validators.BooleanValidator()]
        ),
        ModuleOption(
            name="ExtractCommitter",
            default=True,
            required=True,
            description="Whether to extract committer information",
            validators=[validators.BooleanValidator()]
        ),
    ],
    dependencies=[]
)

