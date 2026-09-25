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
    name="GitHub User Miner",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        'Tim Tomes (@lanmaster53)',
],
    required_keys=["github_api"],
    version="2.0.0",
    description="Uses the GitHub API to gather user information from harvested profiles. Updated the 'contacts' table"
                "with the results",
    query="SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL and resource LIKE 'GitHub'",
    options=[],
    dependencies=[]
)

