import os, json, datetime, logging, requests, urllib3
import azure.functions as func
from azure.storage.blob import BlobServiceClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STORAGE_CONN = os.environ["AZURE_STORAGE_CONN"]

def main(mytimer: func.TimerRequest) -> None:
    now = datetime.datetime.utcnow()
    y, m, d = now.year, f"{now.month:02d}", f"{now.day:02d}"
    ts_iso = now.isoformat()

    # ── llamada a la API ───────────────────────────────────────────
    url  = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias"
    resp = requests.get(url, timeout=10, verify=False)   # ← desactiva SSL
    resp.raise_for_status()
    data = resp.json()

    # ── destino en ADLS Gen2 ──────────────────────────────────────
    blob_path = (
        f"raw/monetarias/year={y}/month={m}/day={d}/"
        f"vars_{ts_iso}.json"
    )
    blob_service = BlobServiceClient.from_connection_string(STORAGE_CONN)
    blob_service.get_container_client("datalake").upload_blob(
        name=blob_path,
        data=json.dumps(data),
        overwrite=True,
    )
    logging.info("Saved %d records → %s", len(data), blob_path)

