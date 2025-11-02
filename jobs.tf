# Jobs and CronJobs
# Task 2.2: Jobs and CronJobs for one-time and scheduled tasks
#
# Jobs run to completion (one-time tasks)
# CronJobs run on a schedule (recurring tasks)

# One-time Job: Cleanup old logs
# This job can be triggered manually to clean up old log files
resource "kubernetes_job" "cleanup_logs" {
  count = var.enable_jobs ? 1 : 0

  metadata {
    name      = "${var.app_name}-cleanup-logs"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app     = var.app_name
      env     = var.environment
      job-type = "cleanup"
    }
  }

  spec {
    # Job will be deleted after 24 hours if not manually cleaned up
    ttl_seconds_after_finished = 86400

    template {
      metadata {
        labels = {
          app     = var.app_name
          env     = var.environment
          job-type = "cleanup"
        }
      }

      spec {
        restart_policy = "OnFailure"  # Retry on failure, but don't restart on success

        container {
          name  = "cleanup"
          image = "busybox:1.36"

          command = [
            "sh",
            "-c",
            <<-EOT
              echo "Starting log cleanup job..."
              echo "This is a demo cleanup job that simulates log rotation"
              echo "In production, this would remove old log files"
              
              # Simulate cleanup work
              echo "Cleaning up logs older than 7 days..."
              sleep 5
              
              echo "Cleanup completed successfully!"
              echo "Job finished at $(date)"
            EOT
          ]

          resources {
            requests = {
              cpu    = "50m"
              memory = "64Mi"
            }
            limits = {
              cpu    = "200m"
              memory = "128Mi"
            }
          }
        }
      }
    }
  }
}

# CronJob: Daily log rotation
# Runs every day at 2 AM to rotate logs
resource "kubernetes_cron_job" "daily_log_rotation" {
  count = var.enable_cronjobs ? 1 : 0

  metadata {
    name      = "${var.app_name}-daily-log-rotation"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app     = var.app_name
      env     = var.environment
      job-type = "maintenance"
    }
  }

  spec {
    # Cron schedule: Run daily at 2:00 AM
    # Format: minute hour day month weekday
    schedule = var.cronjob_schedule

    # Time zone (optional, defaults to controller timezone)
    time_zone = "UTC"

    # How many successful and failed jobs to keep
    successful_jobs_history_limit = 3
    failed_jobs_history_limit    = 1

    # Starting deadline: Job must start within this time after scheduled time
    starting_deadline_seconds = 300  # 5 minutes

    # Job template (what to run)
    job_template {
      metadata {
        labels = {
          app     = var.app_name
          env     = var.environment
          job-type = "maintenance"
        }
      }

      spec {
        # Job will be deleted after 24 hours
        ttl_seconds_after_finished = 86400

        template {
          metadata {
            labels = {
              app     = var.app_name
              env     = var.environment
              job-type = "maintenance"
            }
          }

          spec {
            restart_policy = "OnFailure"

            container {
              name  = "log-rotation"
              image = "busybox:1.36"

              command = [
                "sh",
                "-c",
                <<-EOT
                  echo "Starting daily log rotation..."
                  echo "Scheduled time: $(date)"
                  echo "This job simulates log rotation for the application"
                  
                  # Simulate log rotation work
                  echo "Archiving logs older than 30 days..."
                  echo "Compressing log files..."
                  sleep 10
                  
                  echo "Log rotation completed successfully!"
                  echo "Job finished at $(date)"
                EOT
              ]

              resources {
                requests = {
                  cpu    = "100m"
                  memory = "128Mi"
                }
                limits = {
                  cpu    = "500m"
                  memory = "256Mi"
                }
              }
            }
          }
        }
      }
    }
  }
}

# CronJob: Health check report
# Runs every hour to generate a health check report
resource "kubernetes_cron_job" "health_check_report" {
  count = var.enable_cronjobs ? 1 : 0

  metadata {
    name      = "${var.app_name}-health-check-report"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app     = var.app_name
      env     = var.environment
      job-type = "monitoring"
    }
  }

  spec {
    # Run every hour at minute 0
    schedule = "0 * * * *"  # Every hour
    time_zone = "UTC"

    successful_jobs_history_limit = 2
    failed_jobs_history_limit    = 1

    starting_deadline_seconds = 600  # 10 minutes

    job_template {
      metadata {
        labels = {
          app     = var.app_name
          env     = var.environment
          job-type = "monitoring"
        }
      }

      spec {
        ttl_seconds_after_finished = 86400

        template {
          metadata {
            labels = {
              app     = var.app_name
              env     = var.environment
              job-type = "monitoring"
            }
          }

          spec {
            restart_policy = "OnFailure"

            container {
              name  = "health-check"
              image = "curlimages/curl:latest"

              command = [
                "sh",
                "-c",
                <<-EOT
                  echo "Generating health check report..."
                  echo "Time: $(date)"
                  
                  # In production, this would check app health endpoints
                  # and generate a report
                  echo "Checking application health..."
                  echo "Report generated successfully"
                  
                  echo "Health check report completed at $(date)"
                EOT
              ]

              resources {
                requests = {
                  cpu    = "50m"
                  memory = "64Mi"
                }
                limits = {
                  cpu    = "200m"
                  memory = "128Mi"
                }
              }
            }
          }
        }
      }
    }
  }
}
