variable "aiven_token" {
    type        = string
    description = "Aiven API token"
    sensitive   = true
}

variable "organization_name" {
    type        = string
    description = "Name of the project"
}

variable "stage" {
    type        = string
    description = "Deployment stage"
    default     = "dev"
}

variable "region" {
    type        = string
    description = "Region to deploy the infrastructure"
    default     = "google-europe-west1"
}

variable "plan" {
    type        = string
    description = "Aiven plan"
    default     = "hobbyist"
}