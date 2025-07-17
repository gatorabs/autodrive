import logging

class SuppressCodesFilter(logging.Filter):
    SUPPRESSED_CODES = (' 200 ', ' 503 ')
    SUPPRESSED_ENDPOINTS = ('/video_feed/', '/api/car-info')

    def filter(self, record):
        msg = record.getMessage()
        return not any(
            code in msg and endpoint in msg
            for code in self.SUPPRESSED_CODES
            for endpoint in self.SUPPRESSED_ENDPOINTS
        )
