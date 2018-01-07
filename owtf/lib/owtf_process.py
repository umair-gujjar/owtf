"""
owtf.lib.owtf_process
~~~~~~~~~~~~~~~~~~~~~

Consists of owtf process class and its manager
"""

import logging
from multiprocessing import Process, Queue
import multiprocessing
import sys

from owtf.utils.file import catch_io_errors, get_log_path
from owtf.utils.formatters import FileFormatter, ConsoleFormatter


class OWTFProcess(Process):
    """
    Implementing own proxy of Process for better control of processes launched
    from OWTF both while creating and terminating the processes
    """

    def __init__(self, **kwargs):
        """
        Ideally not to override this but can be done if needed. If overridden
        please give a call to super() and make sure you run this
        """
        self.poison_q = Queue()
        self._process = None
        self.input_q = None
        self.output_q = None
        self.file_handler = catch_io_errors(logging.FileHandler)
        for key in list(kwargs.keys()):  # Attach all kwargs to self
            setattr(self, key, kwargs.get(key, None))
        super(OWTFProcess, self).__init__()

    def initialize(self, **kwargs):
        """
        Supposed to be overridden if user wants to initialize something
        """
        pass

    def run(self):
        """This method must not be overridden by user

        Sets proper logger with file handler and Formatter
        and launches process specific code

        :return: None
        :rtype: None
        """
        try:
            self.pseudo_run()
        except KeyboardInterrupt:
            # In case of interrupt while listing plugins
            pass

    def pseudo_run(self):
        """
        This method must be overridden by user with the process related code
        """
        pass


    def enable_logging(self, **kwargs):
        """Enables both file and console logging

         . note::

        + process_name <-- can be specified in kwargs
        + Must be called from inside the process because we are kind of
          overriding the root logger

        :param kwargs: Additional arguments to the logger
        :type kwargs: `dict`
        :return:
        :rtype: None
        """
        process_name = kwargs.get("process_name", multiprocessing.current_process().name)
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        file_handler = self.file_handler(get_log_path(process_name), mode="w+")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter())

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(ConsoleFormatter())

        # Replace any old handlers
        logger.handlers = [file_handler, stream_handler]

    def disable_console_logging(self, **kwargs):
        """Disables console logging

        . note::
            Must be called from inside the process because we should remove handler for that root logger. Since we add
            console handler in the last, we can remove the last handler to disable console logging

        :param kwargs: Additional arguments to the logger
        :type kwargs: `dict`
        :return:
        :rtype: None
        """
        logger = logging.getLogger()
        if isinstance(logger.handlers[-1], logging.StreamHandler):
            logger.removeHandler(logger.handlers[-1])