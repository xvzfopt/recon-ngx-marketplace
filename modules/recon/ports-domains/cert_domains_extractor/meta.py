# =====================================================================================
# Imports: External
# =====================================================================================
from recon.sdk import ModuleMetadata

# =====================================================================================
# Imports: Internal
# =====================================================================================

# =====================================================================================
# Module Metadata
# =====================================================================================
meta = ModuleMetadata(
    name="Certificate Domains Extractor",
    authors=[
        'xvzf_opt (@xvzf_opt)'
    ],
    version="1.0.0",
    description="Harvests Domain Names exposed in TLS certificate metadata from web servers running over HTTPS",
    query="SELECT DISTINCT host,port FROM ports WHERE protocol = 'https'",
    options=[
    ],
    dependencies=["cryptography"]
)

