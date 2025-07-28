resource "azurerm_synapse_workspace" "ws" {
  name                = "syn-${random_string.suffix.result}"
  resource_group_name = var.rg_name
  location            = var.location # ← cambiarás var.location en el módulo padre

  storage_data_lake_gen2_filesystem_id = "https://${var.storage_name}.dfs.core.windows.net/datalake"

  identity {
    type = "SystemAssigned" # ← identidad requerida
  }

  sql_identity_control_enabled    = false
  managed_virtual_network_enabled = false
  public_network_access_enabled   = true
}
resource "random_string" "suffix" {
  length  = 4
  lower   = true
  upper   = false # ← DESACTIVAR mayúsculas
  numeric = true
  special = false # ← SIN guiones ni símbolos
}

