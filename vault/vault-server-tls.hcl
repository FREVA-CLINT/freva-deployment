ui = false

listener "tcp" {
  address          = "0.0.0.0:8200"
  tls_disable      = "true"
  #tls_require_and_verify_client_cert="false"
  #tls_cert_file = "/mnt/freva.crt"
  #tls_key_file  = "/mnt/freva.key"
  # This is the certificate that client certs are signed with.  In this demo
  # the same intermediate cert signs both Vault and Client certs.  But 
  # to show this differentiation, we use the ca out of the /client-certs/ dir
  #tls_client_ca_file="./output/client-certs/ca.pem"
}

api_addr="http://127.0.0.1:8200"
storage "file" {
  path = "/vault/file"
}
