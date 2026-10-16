class AppError(Exception):
    """Base class for errors that map cleanly onto an HTTP response."""

    status_code = 500
    code = "internal_error"
    default_message = "Something went wrong. Please try again."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidUrlError(AppError):
    status_code = 400
    code = "invalid_url"
    default_message = "Enter a valid YouTube video link."


class VideoUnavailableError(AppError):
    status_code = 422
    code = "video_unavailable"
    default_message = (
        "This video could not be loaded. It may be private, age-restricted, "
        "region-locked or removed."
    )


class DownloadFailedError(AppError):
    status_code = 500
    code = "download_failed"
    default_message = "The download failed. Please try again."


class JobNotFoundError(AppError):
    status_code = 404
    code = "job_not_found"
    default_message = "This download does not exist or has expired."


class JobNotReadyError(AppError):
    status_code = 409
    code = "job_not_ready"
    default_message = "This download is not finished yet."


class QueueFullError(AppError):
    status_code = 429
    code = "queue_full"
    default_message = "The server is busy. Please try again in a minute."
