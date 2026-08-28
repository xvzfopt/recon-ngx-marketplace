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
    name="IANA Private Enterprise Number Domain Names Extractor",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        "Jonathan M. Wilbur <jonathan@wilbur.space>"
    ],
    required_keys=[],
    version="1.0.0",
    description="Gathers Domain Names from the IANA Private Enterprise Number (PEN) registry for the given "
                "company, adding them to the 'domains' table.",
    query="SELECT DISTINCT company FROM companies WHERE company IS NOT NULL",
    options=[],
    dependencies=[]
)

