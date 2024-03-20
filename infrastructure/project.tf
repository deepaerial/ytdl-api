 # Get information about your organization
 data "aiven_organization" "main" {
  name = var.organization_name
 }
 # Create a new project in your organization
 resource "aiven_project" "ytdl_project" {
  project    = "ytdl"
  parent_id = data.aiven_organization.main.id
 }