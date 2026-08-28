import logging

def setup_logger(logger_name="DevinLogger"):
    """
    Set up the logger for the Devin project.
    Allows specifying a custom logger name.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # Adjust log level as needed (e.g., DEBUG, INFO)
    
    # Create a console handler to display logs in the terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create a file handler to save logs to a file
    file_handler = logging.FileHandler('devin.log')
    file_handler.setLevel(logging.DEBUG)
    
    # Create a formatter for log messages
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set the formatter for both handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
