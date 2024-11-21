from src.automatic_time_lapse_creator_kokoeverest.common.constants import *


class MockResponse:
    status_code = NO_CONTENT_STATUS_CODE


class MockIsDaylight:
    @classmethod
    def false_return(cls):
        return False

    @classmethod
    def true_return(cls):
        return True
