variable "environment" { default = "dev" }
variable "location" { default = "westeurope" }
variable "project" { default = "webapp" }
variable "app_service_sku" { default = "F1" }
variable "log_retention_days" { default = 30 }
variable "enable_sql" { default = false }
variable "enable_postgres" { default = false }
