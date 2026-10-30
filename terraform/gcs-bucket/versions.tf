terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Bootstrap sequence:
  # 1. Run once with -backend=false to create the bucket and local state.
  # 2. Re-run terraform init -migrate-state to move state into this bucket.
  backend "gcs" {
    bucket = "boreal-conquest-421512-terraform-state"
    prefix = "gcs-bucket-bootstrap/terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.location
}
