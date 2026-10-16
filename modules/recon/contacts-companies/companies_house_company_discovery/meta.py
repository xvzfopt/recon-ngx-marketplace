# =====================================================================================
# Imports: External
# =====================================================================================
from recon.sdk import ModuleMetadata
from recon.sdk import ModuleOption
from recon.sdk import validators

# =====================================================================================
# Module Metadata
# =====================================================================================
meta = ModuleMetadata(
    name="Companies House - Company Discovery",
    authors=[
        'xvzf_opt (@xvzf_opt)',
    ],
    version="1.0.0",
    description="Finds companies associated with a contact in the Companies House Register. Updates the 'companies'"
                " table with the result",
    required_keys=["companies_house_api"],
    query="SELECT first_name "
          "|| COALESCE(' ' || NULLIF(middle_name, ''), '') "
          "|| COALESCE(' ' || NULLIF(last_name, ''), '') "
          "AS full_name FROM contacts",
    options=[
        ModuleOption(
            name="ExactMatch",
            required=True,
            default=True,
            description="Whether or not to require an exact match of the officer's name",
            validators=[validators.BooleanValidator()]
        ),
        ModuleOption(
            name="ResultLimit",
            default=10,
            required=False,
            description="Limits the number of results to process",
            validators=[validators.IntegerValidator()]
        )
    ],
    dependencies=[""]
)

