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
