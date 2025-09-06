from typing import Optional, Dict, Any


class BillSplitterException(Exception):
    """Base exception for bill splitter application."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BillSplitterException):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.field = field
        self.value = value
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": value})


class FileProcessingError(BillSplitterException):
    """Exception raised when file processing fails."""
    
    def __init__(self, message: str, filename: Optional[str] = None, file_type: Optional[str] = None):
        self.filename = filename
        self.file_type = file_type
        super().__init__(message, "FILE_PROCESSING_ERROR", {"filename": filename, "file_type": file_type})


class OCRProcessingError(BillSplitterException):
    """Exception raised when OCR processing fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        self.file_path = file_path
        super().__init__(message, "OCR_PROCESSING_ERROR", {"file_path": file_path})


class DataExtractionError(BillSplitterException):
    """Exception raised when data extraction fails."""
    
    def __init__(self, message: str, raw_text: Optional[str] = None):
        self.raw_text = raw_text
        super().__init__(message, "DATA_EXTRACTION_ERROR", {"raw_text": raw_text})


class CalculationError(BillSplitterException):
    """Exception raised when calculation fails."""
    
    def __init__(self, message: str, calculation_type: Optional[str] = None):
        self.calculation_type = calculation_type
        super().__init__(message, "CALCULATION_ERROR", {"calculation_type": calculation_type})


class PersonNotFoundError(BillSplitterException):
    """Exception raised when a person is not found."""
    
    def __init__(self, message: str, person_id: Optional[str] = None):
        self.person_id = person_id
        super().__init__(message, "PERSON_NOT_FOUND", {"person_id": person_id})


class BillNotFoundError(BillSplitterException):
    """Exception raised when a bill is not found."""
    
    def __init__(self, message: str, bill_id: Optional[str] = None):
        self.bill_id = bill_id
        super().__init__(message, "BILL_NOT_FOUND", {"bill_id": bill_id})


class SplitNotFoundError(BillSplitterException):
    """Exception raised when a split calculation is not found."""
    
    def __init__(self, message: str, split_id: Optional[str] = None):
        self.split_id = split_id
        super().__init__(message, "SPLIT_NOT_FOUND", {"split_id": split_id})


class ConfigurationError(BillSplitterException):
    """Exception raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        self.config_key = config_key
        super().__init__(message, "CONFIGURATION_ERROR", {"config_key": config_key})


class ExternalServiceError(BillSplitterException):
    """Exception raised when external service fails."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, status_code: Optional[int] = None):
        self.service_name = service_name
        self.status_code = status_code
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", {"service_name": service_name, "status_code": status_code})
