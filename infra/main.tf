terraform {
  required_version = "~> 1.7"

  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "stgstate23825"   # <── TU storage definitivo
    container_name       = "tfstate"
    key                  = "bcra-demo.tfstate"
  }

  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.53" }
  }
}

provider "azurerm" {
  features {}
}

# placeholder (se elimina luego)
resource "null_resource" "bootstrap" {}

module "cotizaciones_lake" {
  source   = "../modules/storage"

  rg_name  = "tfstate-rg"   # puedes dejar el mismo RG
  location = "eastus"
  prefix   = "cotizaciones" # se convertirá en algo como cotizacionesa1b2
}
module "synapse_ws" {
  source        = "../modules/synapse"
  rg_name       = "tfstate-rg"
  location      = "eastus2"          # ← cambia aquí
  storage_name  = module.cotizaciones_lake.account_name
}
module "ingest_function" {
  source   = "../modules/function_app"
  rg_name  = "tfstate-rg"
  location = "centralus"          # ← región con cuota Y1
  prefix   = "cotiz"
  datalake_account           = module.cotizaciones_lake.account_name
  datalake_connection_string = module.cotizaciones_lake.connection_string
}
