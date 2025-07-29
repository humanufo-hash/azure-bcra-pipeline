import pytest
import json
import os
import requests
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import datetime


class TestIntegration:
    """Tests de integración para el pipeline completo de BCRA"""

    @pytest.fixture
    def storage_client(self):
        """Fixture para cliente de Azure Storage"""
        connection_string = os.environ.get("AZURE_STORAGE_CONN")
        if not connection_string:
            pytest.skip("AZURE_STORAGE_CONN environment variable not set")
        
        return BlobServiceClient.from_connection_string(connection_string)

    @pytest.fixture
    def sample_bcra_data(self):
        """Fixture con datos de ejemplo del BCRA"""
        return [
            {
                "idVariable": 1,
                "cdSerie": "7935",
                "descripcion": "Reservas internacionales del BCRA (en millones de dólares)",
                "fecha": "2025-07-29",
                "valor": 25000.50
            },
            {
                "idVariable": 2,
                "cdSerie": "7936", 
                "descripcion": "Base monetaria",
                "fecha": "2025-07-29",
                "valor": 15000000.75
            }
        ]

    def test_bcra_api_availability(self):
        """Test que verifica que la API del BCRA esté disponible"""
        url = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias"
        
        try:
            response = requests.get(url, timeout=10, verify=False)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            
            # Verificar estructura de datos
            first_item = data[0]
            required_fields = ["idVariable", "cdSerie", "descripcion", "fecha", "valor"]
            for field in required_fields:
                assert field in first_item
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"BCRA API not available: {e}")

    def test_storage_blob_upload_and_event_trigger(self, storage_client, sample_bcra_data):
        """Test de integración completo: subida de blob y trigger de Event Grid"""
        container_name = "datalake"
        now = datetime.datetime.utcnow()
        blob_name = f"raw/monetarias/year={now.year}/month={now.month:02d}/day={now.day:02d}/integration_test_{now.strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # 1. Subir blob de prueba
            blob_data = json.dumps(sample_bcra_data)
            blob_client = storage_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            
            blob_client.upload_blob(blob_data, overwrite=True)
            
            # 2. Verificar que el blob existe
            assert blob_client.exists()
            
            # 3. Verificar contenido del blob
            downloaded_data = blob_client.download_blob().readall()
            parsed_data = json.loads(downloaded_data)
            assert parsed_data == sample_bcra_data
            
            # 4. El Event Grid debería disparar automáticamente
            # (esto se verifica en los logs de Application Insights)
            
        finally:
            # Cleanup: eliminar blob de prueba
            try:
                blob_client.delete_blob()
            except:
                pass

    def test_blob_metadata_extraction(self, storage_client):
        """Test que verifica la extracción correcta de metadata de paths"""
        test_cases = [
            {
                "path": "raw/monetarias/year=2025/month=07/day=29/vars_test.json",
                "expected": {"year": "2025", "month": "07", "day": "29"}
            },
            {
                "path": "raw/monetarias/year=2024/month=12/day=31/vars_test.json", 
                "expected": {"year": "2024", "month": "12", "day": "31"}
            }
        ]
        
        for test_case in test_cases:
            path_parts = test_case["path"].split('/')
            metadata = {}
            
            for part in path_parts:
                if part.startswith('year='):
                    metadata['year'] = part.split('=')[1]
                elif part.startswith('month='):
                    metadata['month'] = part.split('=')[1]
                elif part.startswith('day='):
                    metadata['day'] = part.split('=')[1]
            
            assert metadata == test_case["expected"]

    @pytest.mark.slow
    def test_end_to_end_pipeline_simulation(self, storage_client, sample_bcra_data):
        """Test end-to-end que simula el pipeline completo"""
        container_name = "datalake"
        now = datetime.datetime.utcnow()
        
        # 1. Simular ingesta de datos (como lo haría ingest_bcra)
        blob_name = f"raw/monetarias/year={now.year}/month={now.month:02d}/day={now.day:02d}/e2e_test_{now.strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # Subir datos simulando ingest_bcra
            blob_data = json.dumps(sample_bcra_data)
            blob_client = storage_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            upload_result = blob_client.upload_blob(blob_data, overwrite=True)
            assert upload_result is not None
            
            # 2. Verificar que el blob está en la ubicación correcta
            blob_properties = blob_client.get_blob_properties()
            assert blob_properties.size > 0
            assert blob_properties.content_type is not None
            
            # 3. Simular procesamiento (lo que haría blob_alert)
            downloaded_content = blob_client.download_blob().readall()
            processed_data = json.loads(downloaded_content)
            
            # Verificar que los datos son válidos para procesamiento
            assert isinstance(processed_data, list)
            assert len(processed_data) > 0
            
            for item in processed_data:
                assert "idVariable" in item
                assert "cdSerie" in item
                assert "descripcion" in item
                assert "fecha" in item
                assert "valor" in item
                assert isinstance(item["valor"], (int, float))
            
            # 4. Simular transformación a Parquet (futuro ADF)
            # Por ahora solo verificamos que los datos son transformables
            parquet_ready_data = []
            for item in processed_data:
                transformed_item = {
                    "id_variable": item["idVariable"],
                    "codigo_serie": item["cdSerie"],
                    "descripcion": item["descripcion"],
                    "fecha": datetime.datetime.strptime(item["fecha"], "%Y-%m-%d"),
                    "valor": float(item["valor"])
                }
                parquet_ready_data.append(transformed_item)
            
            assert len(parquet_ready_data) == len(processed_data)
            
        finally:
            # Cleanup
            try:
                blob_client.delete_blob()
            except:
                pass

    def test_event_grid_subscription_configuration(self):
        """Test que verifica la configuración del Event Grid subscription"""
        # Este test requiere Azure CLI configurado
        import subprocess
        
        try:
            result = subprocess.run([
                "az", "eventgrid", "event-subscription", "show",
                "--name", "monetarias-created",
                "--source-resource-id", "/subscriptions/d510dc95-40fc-419a-97cd-4ca39a6e184e/resourceGroups/tfstate-rg/providers/Microsoft.Storage/storageAccounts/cotizacionesbrfd",
                "--query", "provisioningState",
                "-o", "tsv"
            ], capture_output=True, text=True, check=True)
            
            assert result.stdout.strip() == "Succeeded"
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Azure CLI not available or not configured")

    def test_function_app_health(self):
        """Test que verifica el estado de la Function App"""
        import subprocess
        
        try:
            result = subprocess.run([
                "az", "functionapp", "show",
                "--name", "cotiz-func-o877",
                "--resource-group", "tfstate-rg",
                "--query", "state",
                "-o", "tsv"
            ], capture_output=True, text=True, check=True)
            
            assert result.stdout.strip() == "Running"
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Azure CLI not available or not configured")
