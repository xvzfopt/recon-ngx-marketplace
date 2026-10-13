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
    name="GitHub Dorks Analyzer",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        'Tim Tomes (@lanmaster53)',
    ],
    required_keys=["github_api"],
    version="2.0.0",
    description="Uses the GitHub API to search for possible vulnerabilities in source code using GitHub Dorks and"
                " the 'repo' search operator. Updates the 'vulnerabilities' table with the results.",
    query="SELECT DISTINCT owner || '/' || name FROM repositories WHERE name IS NOT NULL AND resource LIKE 'GitHub'"
          " AND category LIKE 'repo'",
    options=[
        ModuleOption(
            name="DorksFile",
            default="data/github_dorks.txt",
            required=True,
            description="The file containing the list of GitHub Dorks to search (newline-separated)",
            validators=[validators.ValidFileValidator()]
        ),
        ModuleOption(
            name="PageLimit",
            default=1,
            required=True,
            description="Maximum number of result pages to process",
            validators=[validators.IntegerValidator()]
        ),
    ],
    dependencies=[]
)

