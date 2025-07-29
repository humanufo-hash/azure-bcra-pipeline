output "workspace_name" { value = azurerm_synapse_workspace.ws.name }
output "sql_endpoint" { value = "sql.${azurerm_synapse_workspace.ws.name}.sql.azuresynapse.net" }
