import json
import logging
import datetime
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import os

def main(event: func.EventGridEvent):
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
        
        # Here you could add additional processing:
        # - Send notification to external systems
        # - Trigger downstream data processing
        # - Update metadata tables
        # - Validate data quality
        
        # For now, we'll just log successful processing
        logging.info(f"Successfully processed blob creation event for: {blob_name}")
        
        # Optional: Store metadata in Application Insights custom events
        # This will help with monitoring and analytics
        try:
            # Custom telemetry can be added here if needed
            pass
        except Exception as e:
            logging.error(f"Error storing custom telemetry: {e}")
            
    else:
        logging.info(f"Ignoring event - Type: {event_type}, Blob: {blob_name}")
