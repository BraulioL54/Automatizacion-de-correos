import logging

logging.basicConfig(
    filename='envio_correos.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Prueba de log")
logging.error("Esto es un error")