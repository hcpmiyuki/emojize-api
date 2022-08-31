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
    images = ["gcr.io/$PROJECT_ID/$REPO_NAME:$COMMIT_SHA"]
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t",
        "gcr.io/$PROJECT_ID/$REPO_NAME:$COMMIT_SHA",
        "-f",
        "app/Dockerfile",
        "."
      ]
    }

    step {
      id   = "Push"
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push",
        "gcr.io/$PROJECT_ID/$REPO_NAME:$COMMIT_SHA"
      ]
    }
  }
}