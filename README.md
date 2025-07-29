# Azure BCRA Pipeline

Pipeline automatizado para la ingesta, procesamiento y transformación de datos de variables monetarias del Banco Central de la República Argentina (BCRA) en Azure Data Lake.

## 🏗️ Arquitectura

```
BCRA API → Azure Functions → Azure Data Lake → Event Grid → Transformación → Analytics
    ↓              ↓               ↓             ↓              ↓            ↓
  Datos JSON   ingest_bcra    raw/monetarias  blob_alert   Azure ADF    Parquet
```

## 📋 Componentes

### ✅ **Implementados y en Producción**

- **Azure Function App** (`cotiz-func-o877`): Python 3.11, Linux Consumption Plan
- **Azure Storage Account** (`cotizacionesbrfd`): ADLS Gen2 con contenedor `datalake`
- **Application Insights** (`cotiz-func-ai`): Monitoreo y logs
- **Action Group** (`func-alerts`): Notificaciones por email

### 🔄 **Funciones Activas**

1. **`ingest_bcra`** (Timer Trigger)
   - Ejecuta cada hora en el minuto 5
   - Descarga datos de `https://api.bcra.gob.ar/estadisticas/v3.0/monetarias`
   - Almacena en `raw/monetarias/year=YYYY/month=MM/day=DD/vars_<timestamp>.json`

2. **`blob_alert`** (Event Grid Trigger)
   - Se activa cuando se crean nuevos blobs en `raw/monetarias/`
   - Genera notificaciones detalladas
   - Crea telemetría personalizada para monitoreo

### 🆕 **Nuevos Módulos Añadidos**

- **Azure Data Factory**: Pipeline de transformación JSON → Parquet
- **CI/CD con GitHub Actions**: Despliegue automatizado y tests
- **Tests Unitarios e Integración**: Cobertura completa de código
- **Infraestructura como Código**: Terraform para ADF

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.11
- Azure CLI
- Azure Functions Core Tools 4
- Terraform (opcional, para ADF)

### Configuración Local

```bash
# Clonar repositorio
git clone <repository-url>
cd azure-bcra-pipeline

# Instalar dependencias
pip install -r requirements.txt

# Configurar Azure CLI
az login

# Configurar variables de entorno
cp local.settings.json.example local.settings.json
# Editar local.settings.json con tus valores
```

### Variables de Entorno Requeridas

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=...",
    "AZURE_STORAGE_CONN": "DefaultEndpointsProtocol=https;AccountName=...",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

## 🧪 Testing

### Ejecutar Tests Unitarios

```bash
# Todos los tests
pytest

# Solo tests unitarios
pytest -m "not slow"

# Con cobertura
pytest --cov=src --cov=function_app --cov-report=html
```

### Tests de Integración

```bash
# Tests de integración (requieren Azure configurado)
pytest -m integration

# Test end-to-end completo
pytest tests/test_integration.py::TestIntegration::test_end_to_end_pipeline_simulation
```

## 📊 Monitoreo

### Application Insights Queries

```kusto
// Logs de blob_alert
traces
| where timestamp > ago(24h)
| where message contains "blob_alert" or message contains "BCRA_NOTIFICATION"
| order by timestamp desc

// Eventos personalizados
traces
| where timestamp > ago(24h)
| where message contains "CUSTOM_EVENT_BCRA_BLOB_PROCESSED"
| order by timestamp desc

// Errores
exceptions
| where timestamp > ago(24h)
| where cloud_RoleName == "cotiz-func-o877"
| order by timestamp desc
```

### Alertas Configuradas

- **func-runs**: Alerta cuando `FunctionExecutionCount > 0` en 15 min
- **Email**: Notificaciones a `human.ufoo@gmail.com`

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

El pipeline automatizado incluye:

1. **Test Stage**: Tests unitarios y de cobertura
2. **Deploy Stage**: Despliegue de Azure Functions
3. **Infrastructure Stage**: Terraform para ADF
4. **Monitoring Stage**: Health checks post-despliegue

### Configuración de Secrets

Configurar en GitHub Secrets:

```
AZURE_CREDENTIALS: Service Principal JSON
AZURE_SUBSCRIPTION_ID: ID de suscripción
```

## 📁 Estructura del Proyecto

```
azure-bcra-pipeline/
├── .github/workflows/          # GitHub Actions CI/CD
├── infra/                      # Terraform para infraestructura
├── src/functions/              # Funciones Azure (legacy)
├── tests/                      # Tests unitarios e integración
├── function_app.py             # Función principal (v2 model)
├── host.json                   # Configuración Azure Functions
├── requirements.txt            # Dependencias Python
├── pytest.ini                 # Configuración de tests
└── README.md                   # Esta documentación
```

## 🔧 Desarrollo

### Agregar Nueva Función

```python
@app.function_name("nueva_funcion")
@app.route(route="nueva", methods=["GET", "POST"])
def nueva_funcion(req: func.HttpRequest) -> func.HttpResponse:
    # Implementación
    pass
```

### Despliegue Manual

```bash
# Desplegar función
func azure functionapp publish cotiz-func-o877

# Verificar despliegue
az functionapp function list --name cotiz-func-o877 --resource-group tfstate-rg
```

## 📈 Próximos Pasos

### Transformación de Datos (En Desarrollo)

- **Azure Data Factory**: Pipeline JSON → Parquet
- **Particionamiento**: Optimización por fecha
- **Compresión**: Snappy para mejor performance

### Analytics y Reporting

- **Azure Synapse**: Data warehouse para analytics
- **Power BI**: Dashboards ejecutivos
- **Databricks**: ML y análisis avanzado

### Governanza de Datos

- **Azure Purview**: Catálogo de datos
- **Data Quality**: Validaciones automáticas
- **Lineage**: Trazabilidad de datos

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error SSL en BCRA API**
   ```python
   # Solución: usar verify=False
   requests.get(url, verify=False)
   ```

2. **Permisos RBAC Storage**
   ```bash
   # Usar account key en lugar de RBAC
   az storage blob list --account-key <key>
   ```

3. **Function App no responde**
   ```bash
   # Restart function app
   az functionapp restart --name cotiz-func-o877 --resource-group tfstate-rg
   ```

## 📞 Soporte

- **Logs**: Application Insights `cotiz-func-ai`
- **Alertas**: Action Group `func-alerts`
- **Email**: human.ufoo@gmail.com

## 📄 Licencia

Este proyecto es de uso interno para BBVA.

---

**Estado**: ✅ Producción  
**Última actualización**: 2025-07-29  
**Versión**: 2.0.0
