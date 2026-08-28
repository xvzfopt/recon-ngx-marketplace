# =====================================================================================
# Imports: External
# =====================================================================================
import socket
import ssl
from cryptography import x509
from cryptography.x509.oid import NameOID
from recon.sdk import BaseModule

# =====================================================================================
# Imports: Module Package
# =====================================================================================

# =====================================================================================
# Module Class: Certificate Domains Extractor
# =====================================================================================
class Module(BaseModule):
    '''
    Certificate Domains Extractor
    '''

    # =====================================================================================
    # Module Functions
    # =====================================================================================
    def preflight(self):
        '''
        Override: Module prelight
        '''
        self._test_results_file = None # Used for Test Cases
        return super().preflight()

    def module_pre(self):
        '''
        Override: Set up module properties and perform any additional validation
        '''
        pass


    def module_run(self, socket_addresses):
        '''
        Override: Module execution
        '''

        # =====================================================================================
        # Iterate HTTPS Services
        # =====================================================================================
        count = 0
        domains = []

        # Build SSL Context
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.check_hostname = False

        # Get Timeout
        timeout = self.get_global_option_value("TIMEOUT")
        self.debug("Timeout: %s" % timeout)

        # Iterate Hosts
        with self.get_progress_bar(len(socket_addresses), unit="targets") as progress:
            for socket_address in socket_addresses:
                host = socket_address[0]
                port = socket_address[1]
                progress.write(f"Target ({count + 1} of {len(socket_addresses)}): {host}:{port}")

                # Fetch & process cert
                cert = self.fetch_server_cert(ssl_context, timeout, host, port)
                if cert:
                    for domain in self.extract_cert_domains(cert):
                        if domain not in domains:
                            domains.append(domain)
                            self.insert_domains(domain, mute=True)

                progress.update()
                count += 1

        # # =====================================================================================
        # # Print Summary
        # # =====================================================================================
        self.heading("Summary", level=0)
        self.output("Domain Names found: %s" % len(domains))

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def extract_cert_domains(self, cert):
        '''
        Extracts domain names from an x509 certificate

        :param cert: the target certificate
        :type cert: x509.Certificate
        :returns: List of extracted domain names
        :rtype: list
        '''
        domains = []

        # =====================================================================================
        # Process Cert Common Name
        # =====================================================================================
        cn_attrs = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        for cn_attr in cn_attrs:
            domain = cn_attr.value.strip().lower()
            domain = domain.removeprefix("*.")
            if domain not in domains:
                domains.append(domain)

        # =====================================================================================
        # Process SNA (Subject Alt Name
        # =====================================================================================
        try:
            san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            for domain in san.value.get_values_for_type(x509.DNSName):
                self.debug("Found cert DNS entry: %s" % domain)
                domain = domain.strip().lower()
                domain = domain.removeprefix("*.")
                if domain not in domains:
                    domains.append(domain)
        except x509.ExtensionNotFound as ex:
            self.debug("Could not get cert SAN value: %s" % ex)

        return domains

    def fetch_server_cert(self, ssl_context, timeout, host, port):
        '''
        Fetches the x509 Certificate for the given server address

        :param ssl_context: The SSL Context to use for the connection
        :type ssl_context: ssl.SSLContext
        :param timeout: The timeout to use for the connection
        :type timeout: int
        :param host: Server address
        :type host: str
        :param port: Server port
        :type port: int
        '''
        cert = None

        # =====================================================================================
        # Fetch cert
        # =====================================================================================
        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                with ssl_context.wrap_socket(sock) as tls_sock:
                    cert_der = tls_sock.getpeercert(binary_form=True)
                    cert = x509.load_der_x509_certificate(cert_der)
        except (TimeoutError, socket.gaierror, ssl.SSLEOFError, ssl.SSLError) as ex:
            self.debug("Could not get cert from server: %s" % ex)

        return cert