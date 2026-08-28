#!/bin/bash
# =====================================================================================
# Generates x509 HTTPS certificate used by test case HTTP server
# =====================================================================================
# Set Paths
TEST_ROOT_PATH=`dirname $(realpath "$0")`

# Generate
openssl req \
    -x509 \
    -newkey rsa:2048 \
    -nodes \
    -keyout $TEST_ROOT_PATH/key.pem \
    -out $TEST_ROOT_PATH/cert.pem \
    -days 30 \
    -config $TEST_ROOT_PATH/cert.conf

echo "[+] Certificate generated."