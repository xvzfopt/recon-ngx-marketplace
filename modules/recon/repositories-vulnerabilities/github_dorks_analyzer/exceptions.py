# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.sdk.exceptions import ModuleRuntimeException

# =====================================================================================
# API Rate Limit Exceeded
# =====================================================================================
class APIRateLimitExceeded(ModuleRuntimeException):
    '''
    To be raised in the event that an API Rate Limit is exceeded
    '''
