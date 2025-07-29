resource "azurerm_storage_account" "fa_storage" {
  name                     = "${var.prefix}funcsa${random_string.suffix.result}"
  resource_group_name      = var.rg_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_linux_function_app" "func" {
  name                       = "${var.prefix}-func-${random_string.suffix.result}"
  resource_group_name        = var.rg_name
  location                   = var.location
  storage_account_name       = azurerm_storage_account.fa_storage.name
  storage_account_access_key = azurerm_storage_account.fa_storage.primary_access_key
  service_plan_id            = azurerm_service_plan.plan.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "BCRA_TOKEN"         = "REEMPLAZAR_LUEGO"
    "AZURE_STORAGE_CONN" = var.datalake_connection_string
  }
}

resource "azurerm_service_plan" "plan" {
  name                = "${var.prefix}-plan"
  location            = var.location
  resource_group_name = var.rg_name
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption (gratis)
}
resource "random_string" "suffix" {
  length  = 4
  lower   = true
  numeric = true
  upper   = false
  special = false
}
