import logging

class Logger:
    def __init__(self, logger_type):
        self.logger_type = logger_type.upper()

        logger_dict = logging.Logger.manager.loggerDict
        if self.logger_type in logger_dict:
            self.logger = logging.getLogger(self.logger_type)
            return
        
        self.logger = logging.getLogger(self.logger_type)

        formatter = logging.Formatter(fmt='[%(levelname)s] - %(asctime)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        filename =  f'logs\{self.logger_type}.log'
        handler = logging.FileHandler(filename)        
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_info(self, id, message):
        self.logger.info(f'{id} - {message}')

    def log_error(self, id, message):
        self.logger.error(f'{id} - {message}')

    def log_warning(self, id, message):
        self.logger.warning(f'{id} - {message}')

if __name__ == "__main__":
    server_logger = Logger('SERVER')
    server_logger_2 = Logger('SERVER')
    client_logger = Logger('CLIENT')

    server_a_message = "Client 123 sent message: Hello, with subject: Hey to server A"
    server_b_message = "Client 234 sent message: Hello, with subject: Hey to server B"

    client_123_message = "Connected to server A"
    client_234_message = "Connected to server B"
    client_logger.log_info(id='123', message=client_123_message)
    client_logger.log_info(id='234', message=client_234_message)
    server_logger.log_info(id='A', message=server_a_message)
    server_logger.log_info(id='B', message=server_b_message)

    print(logging.Logger.manager.loggerDict)
