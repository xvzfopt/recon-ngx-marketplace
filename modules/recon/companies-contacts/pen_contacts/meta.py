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
    name="IANA Private Enterprise Number Contact Extractor",
    authors=[
        'xvzf_opt (@xvzf_opt)',
        "Jonathan M. Wilbur <jonathan@wilbur.space>"
    ],
    required_keys=[],
    version="1.0.0",
    description="Gathers contact information from the IANA Private Enterprise Number (PEN) registry for the given "
                "company. Adds contact details to the 'contacts' table.",
    query="SELECT DISTINCT company FROM companies WHERE company IS NOT NULL",
    options=[],
    dependencies=[]
)

