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
    name='Interesting Files Finder',
    authors=[
        'xvzf_opt (https://x.com/xvzf_opt)',
        'Tim Tomes (@lanmaster53)',
        'thrapt (thrapt@gmail.com)',
        'Jay Turla (@shipcod3), and Mark Jeffery'
    ],
    version='3.0',
    description='Checks hosts for interesting files in predictable locations.',
    comments=[
        'Files: robots.txt, sitemap.xml, sitemap.xml.gz, crossdomain.xml, phpinfo.php, test.php, '
        'elmah.axd, server-status, jmx-console/, admin-console/, web-console/ '
        '.well-known/security.txt, .well-known/assetlinks.json, humans.txt, manifest.json '
        'apple-app-site-association, openapi.json, swagger.json, swagger/v1/swagger.json '
        '.git/HEAD',
        'CSV Default: interesting_files_verify.csv',
        'Google Dork Examples:',
        '\tinurl:robots.txt ext:txt',
        '\tinurl:elmah.axd ext:axd intitle:"Error log for"',
        '\tinurl:server-status "Apache Status"'
    ],
    query='SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL',
    options=[
        ModuleOption(name='csv_file', default='data/interesting_files_verify.csv', required=True,
                     description="Custom filename map", validators=[validators.ValidFileValidator]),
        ModuleOption(name='download', default=True, required=True, description='download discovered files',
                     validators=[validators.BooleanValidator]),
        ModuleOption(name='protocol', default='https', required=True, description='request protocol',
                     validators=[validators.ProtocolHTTPSValidator]),
        ModuleOption(name='port', default=443, required=True, description='request port',
                     validators=[validators.PortNumberValidator])
    ]
)
