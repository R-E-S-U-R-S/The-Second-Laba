class StreamStatsError(Exception):
    """Base error"""

class UnsuportedFormatError(StreamStatsError):
    """Unknown or unsupported format. Please enter Jsonl of CSV file"""

class BrokenFileLines(StreamStatsError):
    """Error for broken input files"""

class InvalidEventError(StreamStatsError):
    """Error in evaluation proces"""

class InvalidTimestampError(StreamStatsError):
    """Error in time evaluation proces"""