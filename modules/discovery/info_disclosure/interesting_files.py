# =====================================================================================
# Imports: External
# =====================================================================================
import csv
import os
import warnings
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout
from requests.exceptions import ConnectTimeout
from recon.sdk.exceptions import ModuleValidationException
from recon.sdk import validators
from recon.sdk import BaseModule
from recon.sdk import ModuleMetadata
from recon.sdk import ModuleOption
from recon.sdk import utils

# =====================================================================================
# Module Class: Interesting Files Finder
# =====================================================================================
class Module(BaseModule):
    '''
    Interesting Files Finder
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    meta = ModuleMetadata(
        name='Interesting Files Finder',
        authors=[
            'xvzf_opt (https://x.com/xvzf_opt)',
            'Tim Tomes (@lanmaster53)',
            'thrapt (thrapt@gmail.com)',
            'Jay Turla (@shipcod3), and Mark Jeffery'
        ],
        version='2.0',
        description='Checks hosts for interesting files in predictable locations.',
        comments= [
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
        options = [
            ModuleOption(name='csv_file', default='interesting_files_verify.csv', required=True, description="Custom filename map", validators=[validators.ValidFileValidator]),
            ModuleOption(name='download', default=True, required=True, description='download discovered files', validators=[validators.BooleanValidator]),
            ModuleOption(name='protocol', default='https', required=True, description='request protocol', validators=[validators.ProtocolHTTPSValidator]),
            ModuleOption(name='port', default=443, required=True, description='request port', validators=[validators.PortNumberValidator])
        ],
        files=['interesting_files_verify.csv']
    )

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def module_pre(self):
        '''
        Override: Set up module properties and perform additional validation
        '''

        # Process Options
        self._download = self.get_option_value("download")
        self._protocol = self.get_option_value("protocol")
        self._port = self.get_option_value("port")
        self._csv_path = os.path.join(self.get_data_path(), self.get_option_value("csv_file"))
        self._downloads_dir = self.get_downloads_path()

        # Ignore unicode warnings when trying to un-gzip text type 200 repsonses
        warnings.simplefilter("ignore")

    def module_run(self, hosts):
        '''
        Override: Module runner

        :param hosts: The lists of hosts for which interesting files will be retrieved
        :type hosts: list
        '''
        interesting_files = self.load_interesting_files()
        total_iterations = len(hosts) * len(interesting_files)
        downloaded_files = {}
        count = 0

        # =====================================================================================
        # Iterate Hosts
        # =====================================================================================
        with self.get_progress_bar(total_iterations, unit="files") as progress:
            for host in hosts:

                # For each host, iterate interesting files list
                for filename, verification_string in interesting_files:
                    progress.update()
                    status = "Error"

                    # Build URL
                    url = f"{self._protocol}://{host}:{self._port}/{filename}"

                    # Try to fetch file
                    try:
                        resp = self.request('GET', url)
                        status = resp.status_code
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    # Handle Connection Timeouts
                    except (ReadTimeout, ConnectTimeout):
                        self.debug(f"Connection timeout error: {url}")
                        continue
                    # Handle Connection Errors
                    except ConnectionError:
                        self.debug(f"Connection reset error: {url}")
                        continue

                    # Check for success
                    if status != 200:
                        self.verbose(f"[{status}] {url}")
                        continue

                    # Decompress if needed
                    if ".gz" in filename:
                        text = utils.decompress_gz(resp.text)
                    else:
                        text = resp.text

                    # Verify file contents using verification string
                    if verification_string.lower() not in text.lower():
                        if self.get_verbosity() > 1:
                            progress.write(f"[{status}] {url} => '{filename}' found but unverified.")
                        continue

                    # Download file
                    progress.write(f"[{status}] {url} => '{filename}' found!")
                    if self._download and not filename.endswith("/"):
                        dest_filename = f"{self._protocol}_{host}_{filename.replace('/', '_')}"
                        dest = f"{self._downloads_dir}/{dest_filename}"
                        with open(dest, "w") as out_file:
                            out_file.write(resp.text)
                        downloaded_files[url] = dest_filename
                    count += 1

        # =====================================================================================
        # Print Summary
        # =====================================================================================
        self.output(f"{count} interesting file(s) found.")
        if self._download and count:
            self.output(f"Files downloaded to '{self._downloads_dir}'")

        # Print Downloaded files
        if downloaded_files:
            self.heading(f"Downloaded Files [{len(downloaded_files)}]")
            for file in downloaded_files:
                self.write(f"  > {file} --> {downloaded_files[file]}")
            self.write("")

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
    def load_interesting_files(self):
        '''
        Loads the Interesting filenames file

        :returns: List of interesting files, and their verification string
        :rtype: tuple(str, str
        '''
        interesting_files = []

        with open(self._csv_path) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            try:
                for filename, verification_str in reader:
                    interesting_files.append((filename, verification_str))
            except ValueError:
                raise ModuleValidationException(
                    "Error parsing specified CSV_FILE: %s. Check file format is valid and try again." % self._csv_path
                )

        return interesting_files

