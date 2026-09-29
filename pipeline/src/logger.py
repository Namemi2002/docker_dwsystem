import sys
import warnings

original_stdout = sys.stdout
original_stderr = sys.stderr


class LoggerStdout:

    def __init__(self, db_connection, runtime):
        self.db_connection = db_connection
        self.runtime = runtime

    def write(self, message):
        original_stdout.write(message)
        if message.strip():
            if len(message) > 2000:
                truncate_message = message[0:2000]
            else:
                truncate_message = message
            log_data = [self.runtime, truncate_message, 'print']
            cursor = self.db_connection.cursor()
            try:
                cursor.execute(
                    'INSERT INTO pipelines_runtime_log '
                    '(runtime, message, printtype) VALUES (%s,%s,%s)',
                    log_data
                )
                self.db_connection.commit()
            finally:
                cursor.close()
        else:
            return None
    def flush(self):
        original_stdout.flush()


class LoggerStderr:

    def __init__(self, db_connection, runtime):
        self.db_connection = db_connection
        self.runtime = runtime

    def write(self, message):
        original_stderr.write(message)
        if message.strip():
            if len(message) > 2000:
                truncate_message = message[0:2000]
            else:
                truncate_message = message
            log_data = [self.runtime, truncate_message, 'warning']
            cursor = self.db_connection.cursor()
            try:
                cursor.execute(
                    'INSERT INTO pipelines_runtime_log '
                    '(runtime, message, printtype) VALUES (%s,%s,%s)',
                    log_data
                )
                self.db_connection.commit()
            finally:
                cursor.close()
        else:
            return None
    def flush(self):
        original_stderr.flush()


def custom_formatwarning(
    message,
    category,
    filename,
    lineno,
    file=None,
    line=None,
):
    return f"{message}\n"
