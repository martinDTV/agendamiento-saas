terraform {
  required_version = ">= 1.5.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    namedotcom = {
      source  = "namedotcom/namedotcom"
      version = "~> 1.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

provider "namedotcom" {
  username = var.namecom_user
  token    = var.namecom_token
}
