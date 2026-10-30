terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "REPLACE_WITH_TERRAFORM_STATE_BUCKET"
    prefix = "gcp-sot/foundation.tfstate"
  }
}

provider "google" {}
