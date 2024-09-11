import logging

import anim


class Test_Log:
    def test_init(self):
        logger = anim.log.create_logger()

        assert logger.name == "anim"
        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_other_level(self):
        logger = anim.log.create_logger(level="INFO")

        assert logger.name == "anim"
        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.INFO

    def test_change_level(self):
        logger = anim.log.create_logger()  # noqa: F841

        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

        logger = anim.log.create_logger(level="WARNING")  # noqa: F841

        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.WARNING
