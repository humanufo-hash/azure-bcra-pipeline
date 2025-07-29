# Azure Data Factory para transformación de datos BCRA
resource "azurerm_data_factory" "bcra_adf" {
  name                = "bcra-adf-${random_string.suffix.result}"
  location            = var.location
  resource_group_name = var.resource_group_name

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = "production"
    Project     = "bcra-pipeline"
    Component   = "data-factory"
  }
}

# Linked Service para Azure Data Lake Storage Gen2
resource "azurerm_data_factory_linked_service_azure_blob_storage" "adls_linked_service" {
  name                = "ls_adls_bcra"
  data_factory_id     = azurerm_data_factory.bcra_adf.id
  connection_string   = azurerm_storage_account.bcra_storage.primary_connection_string
}

# Dataset para archivos JSON de origen
resource "azurerm_data_factory_dataset_json" "json_source_dataset" {
  name                = "ds_json_monetarias_source"
  data_factory_id     = azurerm_data_factory.bcra_adf.id
  linked_service_name = azurerm_data_factory_linked_service_azure_blob_storage.adls_linked_service.name

  azure_blob_storage_location {
    container = "datalake"
    path      = "raw/monetarias"
    filename  = "*.json"
  }

  parameters = {
    year  = ""
    month = ""
    day   = ""
  }
}

# Dataset para archivos Parquet de destino
resource "azurerm_data_factory_dataset_parquet" "parquet_sink_dataset" {
  name                = "ds_parquet_monetarias_sink"
  data_factory_id     = azurerm_data_factory.bcra_adf.id
  linked_service_name = azurerm_data_factory_linked_service_azure_blob_storage.adls_linked_service.name

  azure_blob_storage_location {
    container = "datalake"
    path      = "processed/monetarias/year=@{dataset().year}/month=@{dataset().month}/day=@{dataset().day}"
    filename  = "monetarias_@{formatDateTime(utcnow(), 'yyyyMMdd_HHmmss')}.parquet"
  }

  parameters = {
    year  = ""
    month = ""
    day   = ""
  }
}

# Pipeline de transformación
resource "azurerm_data_factory_pipeline" "bcra_transform_pipeline" {
  name            = "pipeline-bcra-monetarias-transform"
  data_factory_id = azurerm_data_factory.bcra_adf.id
  description     = "Pipeline para transformar datos JSON de BCRA a formato Parquet optimizado"

  parameters = {
    year  = "@formatDateTime(utcnow(), 'yyyy')"
    month = "@formatDateTime(utcnow(), 'MM')"
    day   = "@formatDateTime(utcnow(), 'dd')"
  }

  activities_json = jsonencode([
    {
      name = "CopyJSONToParquet"
      type = "Copy"
      dependsOn = []
      policy = {
        timeout = "7.00:00:00"
        retry   = 3
        retryIntervalInSeconds = 30
      }
      typeProperties = {
        source = {
          type = "JsonSource"
          storeSettings = {
            type = "AzureBlobFSReadSettings"
            recursive = true
            wildcardFolderPath = "raw/monetarias/year=@{pipeline().parameters.year}/month=@{pipeline().parameters.month}/day=@{pipeline().parameters.day}"
            wildcardFileName = "vars_*.json"
          }
        }
        sink = {
          type = "ParquetSink"
          storeSettings = {
            type = "AzureBlobFSWriteSettings"
          }
        }
        enableStaging = false
      }
      inputs = [
        {
          referenceName = azurerm_data_factory_dataset_json.json_source_dataset.name
          type = "DatasetReference"
          parameters = {
            year  = "@pipeline().parameters.year"
            month = "@pipeline().parameters.month"
            day   = "@pipeline().parameters.day"
          }
        }
      ]
      outputs = [
        {
          referenceName = azurerm_data_factory_dataset_parquet.parquet_sink_dataset.name
          type = "DatasetReference"
          parameters = {
            year  = "@pipeline().parameters.year"
            month = "@pipeline().parameters.month"
            day   = "@pipeline().parameters.day"
          }
        }
      ]
    }
  ])
}

# Trigger para ejecutar el pipeline automáticamente
resource "azurerm_data_factory_trigger_schedule" "daily_transform_trigger" {
  name            = "trigger-daily-transform"
  data_factory_id = azurerm_data_factory.bcra_adf.id
  pipeline_name   = azurerm_data_factory_pipeline.bcra_transform_pipeline.name

  frequency = "Hour"
  interval  = 1
  start_time = "2025-07-29T16:00:00Z"

  schedule {
    hours   = [16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    minutes = [15] # 10 minutos después de la ingesta
  }

  pipeline_parameters = {
    year  = "@formatDateTime(utcnow(), 'yyyy')"
    month = "@formatDateTime(utcnow(), 'MM')"
    day   = "@formatDateTime(utcnow(), 'dd')"
  }

  annotations = ["BCRA", "Hourly", "Transform"]
}

# Role assignment para que ADF pueda acceder al storage
resource "azurerm_role_assignment" "adf_storage_contributor" {
  scope                = azurerm_storage_account.bcra_storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.bcra_adf.identity[0].principal_id
}

# Variables de salida
output "data_factory_name" {
  description = "Nombre del Azure Data Factory"
  value       = azurerm_data_factory.bcra_adf.name
}

output "data_factory_id" {
  description = "ID del Azure Data Factory"
  value       = azurerm_data_factory.bcra_adf.id
}
