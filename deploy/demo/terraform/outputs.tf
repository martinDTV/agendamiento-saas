output "droplet_ip" {
  description = "Public IP of the demo droplet"
  value       = digitalocean_droplet.demo.ipv4_address
}

output "demo_domain" {
  description = "Apex demo host"
  value       = local.demo_domain
}

output "example_clinic_url" {
  description = "What a clinic demo URL looks like"
  value       = "https://clinica-del-norte.${local.demo_domain}"
}
