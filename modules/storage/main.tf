# Genera un sufijo aleatorio para que el nombre sea único en Azure
resource "random_string" "suffix" {
  length  = 4
  lower   = true
  upper   = false
  numeric = true
}

# Storage Account con ADLS Gen2 habilitado
resource "azurerm_storage_account" "datalake" {
  name                     = "${var.prefix}${random_string.suffix.result}"
  resource_group_name      = var.rg_name
  location                 = var.location

  account_tier             = "Standard"
  account_replication_type = "LRS"

  is_hns_enabled           = true       # << habilita el namespace jerárquico (Gen2)
}

# Filesystem interno llamado "datalake"
resource "azurerm_storage_data_lake_gen2_filesystem" "lake" {
  name               = "datalake"
  storage_account_id = azurerm_storage_account.datalake.id
}

