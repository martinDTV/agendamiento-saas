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
    namecom_user         = var.namecom_user
    namecom_token        = var.namecom_token
    repo_url             = var.repo_url
    repo_branch          = var.repo_branch
  })

  tags = ["agendamiento", "demo"]
}

# name.com DNS — managed at the apex zone (var.root_domain).
# Host values are relative to the zone, so we use the subdomain labels only.

# demo-agendamiento.nexosoftdev.com  -> droplet
resource "namedotcom_record" "demo_apex" {
  domain_name = var.root_domain
  host        = var.demo_subdomain
  record_type = "A"
  answer      = digitalocean_droplet.demo.ipv4_address
  ttl         = 300
}

# *.demo-agendamiento.nexosoftdev.com -> droplet (every clinic subdomain)
resource "namedotcom_record" "demo_wildcard" {
  domain_name = var.root_domain
  host        = "*.${var.demo_subdomain}"
  record_type = "A"
  answer      = digitalocean_droplet.demo.ipv4_address
  ttl         = 300
}
