resource "aiven_pg" "pg" {
  project                 = aiven_project.ytdl_project.project
  cloud_name              = var.region
  plan                    = var.plan
  service_name            = "ytdl-db"
  maintenance_window_dow  = "monday"
  maintenance_window_time = "10:00:00"

  pg_user_config {
    pg {
      idle_in_transaction_session_timeout = 900
      log_min_duration_statement          = -1
    }
  }
}