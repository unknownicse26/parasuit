'''Logging module for parasuit library

Logging module for parasuit library. All loggings in parasuit library use this module.
'''

import logging as _logging


_LOGGER = None


def get_logger():
    '''Get a logger.

    Get a singleton `Logger`. If `Logger` not defined make one and return. If `get_logger` called
    previously, returns a `Logger` object created previously.

    Returns:
        A `Logger` object.
    '''

    global _LOGGER
    if not _LOGGER:
        _LOGGER = _logging.getLogger('parasuit')
        if not _logging.getLogger().handlers:
            formatter = _logging.Formatter(fmt='%(asctime)s parasuit [%(levelname)s] %(message)s',
                                           datefmt='%Y-%m-%d %H:%M:%S')
            stderr_handler = _logging.StreamHandler()
            stderr_handler.setFormatter(formatter)
            _LOGGER.addHandler(stderr_handler)
            _LOGGER.setLevel('INFO')
    return _LOGGER
