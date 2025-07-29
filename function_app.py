import azure.functions as func
import datetime
import json
import logging

app = func.FunctionApp()

@app.event_grid_trigger(arg_name="event")
def blob_alert(event: func.EventGridEvent):
    """
    Event Grid trigger function for blob creation events.
    Triggered when new blobs are created in the datalake container
    with prefix raw/monetarias/
    """
    
    logging.info('Python EventGrid trigger processed an event')
    
    # Parse the Event Grid event
    event_data = event.get_json()
    
    # Extract blob information
    blob_url = event_data.get('url', '')
    blob_name = event_data.get('subject', '').replace('/blobServices/default/containers/datalake/blobs/', '')
    event_type = event_data.get('eventType', '')
    event_time = event_data.get('eventTime', '')
    
    logging.info(f"Event Type: {event_type}")
    logging.info(f"Blob Name: {blob_name}")
    logging.info(f"Blob URL: {blob_url}")
    logging.info(f"Event Time: {event_time}")
    
    # Only process BlobCreated events for monetarias data
    if event_type == 'Microsoft.Storage.BlobCreated' and 'raw/monetarias/' in blob_name:
        
        # Extract metadata from blob path
        # Expected format: raw/monetarias/year=YYYY/month=MM/day=DD/vars_timestamp.json
        path_parts = blob_name.split('/')
        
        metadata = {
            'blob_name': blob_name,
            'blob_url': blob_url,
            'event_time': event_time,
            'processed_time': datetime.datetime.utcnow().isoformat(),
            'data_source': 'bcra_monetarias',
            'event_type': event_type
        }
        
        # Extract date information if available
        try:
            for part in path_parts:
                if part.startswith('year='):
                    metadata['year'] = part.split('=')[1]
                elif part.startswith('month='):
                    metadata['month'] = part.split('=')[1]
                elif part.startswith('day='):
                    metadata['day'] = part.split('=')[1]
        except Exception as e:
            logging.warning(f"Could not parse date from path: {e}")
        
        # Log the metadata for monitoring
        logging.info(f"Processed blob metadata: {json.dumps(metadata, indent=2)}")
        
        # Send detailed notification with metadata
        notification_message = f"""
🔔 BCRA Pipeline Alert - Nuevo archivo procesado

📁 Archivo: {blob_name}
🕐 Hora del evento: {event_time}
🕐 Hora de procesamiento: {metadata['processed_time']}
📊 Fuente: {metadata['data_source']}
🔗 URL: {blob_url}

📅 Fecha: {metadata.get('year', 'N/A')}-{metadata.get('month', 'N/A')}-{metadata.get('day', 'N/A')}

✅ Estado: Procesado exitosamente
🏛️ Pipeline: Azure BCRA Monetarias
        """
        
        # Log the detailed notification
        logging.info(f"BCRA_NOTIFICATION: {notification_message}")
        
        # Create custom telemetry event for Application Insights
        custom_properties = {
            'blob_name': blob_name,
            'event_type': event_type,
            'data_source': metadata['data_source'],
            'year': metadata.get('year', ''),
            'month': metadata.get('month', ''),
            'day': metadata.get('day', ''),
            'notification_sent': 'true'
        }
        
        # Log custom event for monitoring dashboard
        logging.info(f"CUSTOM_EVENT_BCRA_BLOB_PROCESSED: {json.dumps(custom_properties)}")
        
        # For future enhancement: Send to external notification systems
        # - Teams webhook
        # - Slack notification  
        # - Email via SendGrid
        # - SMS via Twilio
        
        logging.info(f"Successfully processed blob creation event for: {blob_name}")
        
    else:
        logging.info(f"Ignoring event - Type: {event_type}, Blob: {blob_name}")