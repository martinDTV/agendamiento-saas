locals {
  demo_domain = "${var.demo_subdomain}.${var.root_domain}"
}

resource "digitalocean_droplet" "demo" {
  name     = "agendamiento-demo"
  image    = "ubuntu-24-04-x64"
  region   = var.droplet_region
  size     = var.droplet_size
  ssh_keys = [var.ssh_key_fingerprint]

  user_data = templatefile("${path.module}/cloud-init.yaml.tftpl", {
    demo_domain          = local.demo_domain
    demo_tenant_ttl_days = var.demo_tenant_ttl_days
    django_secret_key    = var.django_secret_key
    postgres_password    = var.postgres_password
    acme_email           = var.acme_email
    do_auth_token        = var.do_token
    repo_url             = var.repo_url
    repo_branch          = var.repo_branch
  })

  tags = ["agendamiento", "demo"]
}

# DNS lives in DigitalOcean (nexosoftdev.com uses ns1/ns2/ns3.digitalocean.com).
# The zone already exists, so we reference it instead of creating it.
data "digitalocean_domain" "root" {
  name = var.root_domain
}

# demo-agendamiento.nexosoftdev.com -> droplet
resource "digitalocean_record" "demo_apex" {
  domain = data.digitalocean_domain.root.name
  type   = "A"
  name   = var.demo_subdomain
  value  = digitalocean_droplet.demo.ipv4_address
  ttl    = 300
}

# *.demo-agendamiento.nexosoftdev.com -> droplet (every clinic subdomain)
resource "digitalocean_record" "demo_wildcard" {
  domain = data.digitalocean_domain.root.name
  type   = "A"
  name   = "*.${var.demo_subdomain}"
  value  = digitalocean_droplet.demo.ipv4_address
  ttl    = 300
}
