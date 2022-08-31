terraform {
  required_version = "1.2.8"
  backend "gcs" {
    prefix = "terraform/state"
  }
}

resource "google_cloudbuild_trigger" "push_to_gcr_trigger" {
  github {
    name  = var.github_repo
    owner = var.github_owner

    push {
      branch       = "^${var.github_branch}$"
      invert_regex = false
    }
  }

  build {
    images = ["gcr.io/$PROJECT_ID/$REPO_NAME:latest"]
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t",
        "gcr.io/$PROJECT_ID/$REPO_NAME:latest",
        "-f",
        "app/Dockerfile",
        "."
      ]
      timeout = "3600s"
    }

    step {
      id   = "Push"
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push",
        "gcr.io/$PROJECT_ID/$REPO_NAME:latest"
      ]
      timeout = "3600s"
    }

    timeout = "7200s"
  }
}

resource "google_cloud_run_service" "emojize_api_cloud_run" {
  name     = var.cloud_run_service_name
  location = var.gcp_location

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_name}$/${var.github_repo}:latest"
        ports {
          container_port = 8080
        }
      }
    }
  }
}