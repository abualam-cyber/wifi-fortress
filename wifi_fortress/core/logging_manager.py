
import logging
import os

def setup_logging(log_file="wifi_fortress.log"):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    full_path = os.path.join(log_dir, log_file)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(full_path),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging initialized.")
