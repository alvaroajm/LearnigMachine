# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

LearnigMachine is a machine learning research project aimed at helping medical professionals — particularly radiologists — improve diagnostic accuracy using ML/AI tools running on Turing machines (general-purpose computing environments).

## Current State

The repository is in its earliest stage. No application code exists yet. What is present:

- `.github/workflows/google1.yml` — a GitHub Actions pipeline that builds a Docker image, pushes it to Google Container Registry (GCR), and deploys it to a Google Kubernetes Engine (GKE) cluster on every GitHub **release** event.
- `.gitignore` — currently configured for Java artifacts (`*.class`, `*.jar`, `*.war`, etc.), though the ML domain typically uses Python. Revisit this if the language choice changes.

## Deployment Architecture

The CI/CD pipeline (`google1.yml`) expects:

- **Secrets** set in the repository: `GKE_PROJECT`, `GKE_EMAIL`, `GKE_KEY`
- A `Dockerfile` at the repository root (not yet created)
- Kubernetes manifests at the repository root: `deployment.yml`, `service.yml`, `kustomization.yml` (not yet created)
- Target cluster config: `GKE_ZONE=us-west1-a`, `GKE_CLUSTER=example-gke-cluster`, image name `gke-test`, deployment name `gke-test`

Deployment is triggered only on `release: [created]` events — not on every push.

The pipeline steps are: checkout → authenticate gcloud → configure Docker → `docker build` → `docker push` to GCR → install `kustomize` → `kubectl apply` + rollout status check.

## Development Branch

Active development happens on feature branches. The current working branch is `claude/add-claude-documentation-vmIyA`. The main branch is `master`.
