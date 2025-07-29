import pytest
import json
import datetime
from unittest.mock import Mock, patch
import azure.functions as func
from function_app import blob_alert


class TestBlobAlert:
    """Test suite para la función blob_alert Event Grid trigger"""

    def create_mock_event_grid_event(self, blob_name, event_type="Microsoft.Storage.BlobCreated"):
        """Crea un mock de Event Grid event para testing"""
        event_data = {
            "url": f"https://cotizacionesbrfd.blob.core.windows.net/datalake/{blob_name}",
            "subject": f"/blobServices/default/containers/datalake/blobs/{blob_name}",
            "eventType": event_type,
            "eventTime": datetime.datetime.utcnow().isoformat() + "Z",
            "id": "test-event-id",
            "dataVersion": "1.0"
        }
        
        mock_event = Mock(spec=func.EventGridEvent)
        mock_event.get_json.return_value = event_data
        return mock_event

    @patch('function_app.logging')
    def test_blob_alert_processes_monetarias_blob(self, mock_logging):
        """Test que blob_alert procesa correctamente blobs de monetarias"""
        # Arrange
        blob_name = "raw/monetarias/year=2025/month=07/day=29/vars_2025-07-29T15:30:00Z.json"
        mock_event = self.create_mock_event_grid_event(blob_name)
        
        # Act
        blob_alert(mock_event)
        
        # Assert
        mock_logging.info.assert_called()
        
        # Verificar que se loggearon los datos correctos
        logged_calls = [call.args[0] for call in mock_logging.info.call_args_list]
        
        # Verificar que se procesó el evento
        assert any("Python EventGrid trigger processed an event" in call for call in logged_calls)
        assert any("Successfully processed blob creation event" in call for call in logged_calls)
        
        # Verificar que se extrajo la metadata correctamente
        metadata_calls = [call for call in logged_calls if "Processed blob metadata" in call]
        assert len(metadata_calls) > 0

    @patch('function_app.logging')
    def test_blob_alert_ignores_non_monetarias_blob(self, mock_logging):
        """Test que blob_alert ignora blobs que no son de monetarias"""
        # Arrange
        blob_name = "raw/other/year=2025/month=07/day=29/other_data.json"
        mock_event = self.create_mock_event_grid_event(blob_name)
        
        # Act
        blob_alert(mock_event)
        
        # Assert
        logged_calls = [call.args[0] for call in mock_logging.info.call_args_list]
        assert any("Ignoring event" in call for call in logged_calls)

    @patch('function_app.logging')
    def test_blob_alert_extracts_date_metadata(self, mock_logging):
        """Test que blob_alert extrae correctamente la metadata de fecha"""
        # Arrange
        blob_name = "raw/monetarias/year=2025/month=07/day=29/vars_2025-07-29T15:30:00Z.json"
        mock_event = self.create_mock_event_grid_event(blob_name)
        
        # Act
        blob_alert(mock_event)
        
        # Assert
        logged_calls = [call.args[0] for call in mock_logging.info.call_args_list]
        metadata_calls = [call for call in logged_calls if "Processed blob metadata" in call]
        
        assert len(metadata_calls) > 0
        # El metadata debería contener year=2025, month=07, day=29
        metadata_str = metadata_calls[0]
        assert "2025" in metadata_str
        assert "07" in metadata_str
        assert "29" in metadata_str

    @patch('function_app.logging')
    def test_blob_alert_handles_different_event_types(self, mock_logging):
        """Test que blob_alert maneja diferentes tipos de eventos correctamente"""
        # Arrange
        blob_name = "raw/monetarias/year=2025/month=07/day=29/vars_test.json"
        mock_event = self.create_mock_event_grid_event(blob_name, "Microsoft.Storage.BlobDeleted")
        
        # Act
        blob_alert(mock_event)
        
        # Assert
        logged_calls = [call.args[0] for call in mock_logging.info.call_args_list]
        assert any("Ignoring event" in call for call in logged_calls)

    @patch('function_app.logging')
    def test_blob_alert_creates_custom_telemetry(self, mock_logging):
        """Test que blob_alert crea telemetría personalizada"""
        # Arrange
        blob_name = "raw/monetarias/year=2025/month=07/day=29/vars_test.json"
        mock_event = self.create_mock_event_grid_event(blob_name)
        
        # Act
        blob_alert(mock_event)
        
        # Assert
        logged_calls = [call.args[0] for call in mock_logging.info.call_args_list]
        custom_event_calls = [call for call in logged_calls if "CUSTOM_EVENT_BCRA_BLOB_PROCESSED" in call]
        
        assert len(custom_event_calls) > 0
        
        # Verificar que el custom event contiene las propiedades esperadas
        custom_event_str = custom_event_calls[0]
        assert "blob_name" in custom_event_str
        assert "event_type" in custom_event_str
        assert "data_source" in custom_event_str

    @patch('function_app.logging')
    def test_blob_alert_notification_format(self, mock_logging):
        """Test que blob_alert genera notificaciones con el formato correcto"""
        # Arrange
        blob_name = "raw/monetarias/year=2025/month=07/day=29/vars_test.json"
        mock_event = self.create_mock_event_grid_event(blob_name)
        
        # Act
        blob_alert(mock_event)
        
        # Assert
        logged_calls = [call.args[0] for call in mock_logging.info.call_args_list]
        notification_calls = [call for call in logged_calls if "BCRA_NOTIFICATION" in call]
        
        assert len(notification_calls) > 0
        
        notification_str = notification_calls[0]
        # Verificar que contiene los elementos esperados de la notificación
        assert "BCRA Pipeline Alert" in notification_str
        assert "Nuevo archivo procesado" in notification_str
        assert "📁 Archivo:" in notification_str
        assert "✅ Estado:" in notification_str
