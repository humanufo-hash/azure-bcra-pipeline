output "account_name"  { value = azurerm_storage_account.datalake.name }
output "dfs_endpoint"  { value = azurerm_storage_account.datalake.primary_dfs_endpoint }
output "blob_endpoint" { value = azurerm_storage_account.datalake.primary_blob_endpoint }
