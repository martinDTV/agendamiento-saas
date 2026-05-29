# All secrets are passed at apply time (TF_VAR_* env or a tfvars file that is
# git-ignored). Nothing sensitive is hardcoded.

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "namecom_user" {
  description = "name.com API username"
  type        = string
  sensitive   = true
}

variable "namecom_token" {
  description = "name.com API token"
  type        = string
  sensitive   = true
}

variable "root_domain" {
  description = "Registered apex domain in name.com"
  type        = string
  default     = "nexosoftdev.com"
}

variable "demo_subdomain" {
  description = "Subdomain under root_domain that fronts the demo (wildcard host)"
  type        = string
  default     = "demo-agendamiento"
}

variable "ssh_key_fingerprint" {
  description = "Fingerprint of an SSH key already uploaded to DigitalOcean"
  type        = string
}

variable "droplet_region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "droplet_size" {
  description = "Droplet size slug (s-1vcpu-2gb is plenty for an ephemeral demo)"
  type        = string
  default     = "s-1vcpu-2gb"
}

variable "repo_url" {
  description = "Git URL the droplet clones to build the demo stack"
  type        = string
}

variable "repo_branch" {
  description = "Branch to deploy"
  type        = string
  default     = "master"
}

# These become the deploy/demo/.env on the droplet.
variable "django_secret_key" {
  type      = string
  sensitive = true
}

variable "postgres_password" {
  type      = string
  sensitive = true
}

variable "acme_email" {
  description = "Email for Let's Encrypt registration"
  type        = string
  default     = "hola@nexosoftdev.com"
}

variable "demo_tenant_ttl_days" {
  type    = number
  default = 7
}
