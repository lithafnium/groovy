import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)-15s %(levelname)-8s %(message)s",
    handlers=[
        logging.FileHandler("logs/groovy_bot.log"),
        logging.StreamHandler(),
    ],
)

def print_log(message: str):
    logging.info("[groovybot]: " + str(message))