# nombre del Function App
output "ingest_function_name" {
  value = module.ingest_function.function_name
}

# url base del Function App (por si la necesitas)
output "ingest_function_url" {
  value = module.ingest_function.function_url
}
