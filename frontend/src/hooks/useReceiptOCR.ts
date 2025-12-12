import { useState, useCallback } from 'react';
import { receiptService } from '@/services/receiptService';
import { ReceiptData } from '@/types/bill.types';
import { ApiError } from '@/types/api.types';

export interface ReceiptOCRState {
  isUploading: boolean;
  isProcessing: boolean;
  uploadProgress: number;
  receiptId: string | null;
  rawText: string | null;
  processedData: ReceiptData | null;
  extractedData: any | null; // Raw extracted data even if validation fails
  error: string | null;
  validationError: any | null;
  needsValidation: boolean;
}

export const useReceiptOCR = () => {
  const [state, setState] = useState<ReceiptOCRState>({
    isUploading: false,
    isProcessing: false,
    uploadProgress: 0,
    receiptId: null,
    rawText: null,
    processedData: null,
    extractedData: null,
    error: null,
    validationError: null,
    needsValidation: false,
  });

  /**
   * Upload and process receipt in a single call (stateless).
   * Backend handles: Upload → OCR → AI Extraction → Validation
   */
  const uploadAndProcessReceipt = useCallback(async (file: File) => {
    setState(prev => ({
      ...prev,
      isUploading: true,
      isProcessing: true,
      uploadProgress: 0,
      error: null,
      validationError: null,
      needsValidation: false,
    }));

    try {
      const response = await receiptService.processReceipt(
        file,
        (progress) => {
          setState(prev => ({
            ...prev,
            uploadProgress: progress,
          }));
        }
      );

      setState(prev => ({
        ...prev,
        isUploading: false,
        isProcessing: false,
        uploadProgress: 100,
        processedData: response.processed_data || null,
        extractedData: response.processed_data || null,
        rawText: response.ocr_text || null,
        needsValidation: true, // Always show validation modal
        validationError: null,
      }));

      console.log('[useReceiptOCR] Successfully processed receipt, set needsValidation=true');

      return response;
    } catch (error) {
      const apiError = error as ApiError;
      console.log('[useReceiptOCR] Process receipt error:', apiError);

      // Check if this is a validation error (422)
      if (apiError.status === 422) {
        // Extract the data from error details
        const errorDetails = apiError.details?.detail || apiError.details;
        const extractedData = errorDetails?.extracted_data;
        const rawText = errorDetails?.raw_text;

        console.log('[useReceiptOCR] Validation error detected:', {
          status: apiError.status,
          errorDetails,
          extractedData,
          hasExtractedData: !!extractedData
        });

        setState(prev => ({
          ...prev,
          isUploading: false,
          isProcessing: false,
          uploadProgress: 0,
          validationError: errorDetails || apiError.message,
          extractedData: extractedData || null,
          rawText: rawText || null,
          needsValidation: true,
        }));
      } else {
        setState(prev => ({
          ...prev,
          isUploading: false,
          isProcessing: false,
          uploadProgress: 0,
          error: apiError.message || 'Failed to process receipt',
          needsValidation: false,
        }));
      }
      throw error;
    }
  }, []);

  /**
   * Validate user-corrected receipt data (stateless).
   * No receiptId needed - just validates the corrected data.
   */
  const validateCorrectedData = useCallback(async (correctedData: any) => {
    setState(prev => ({
      ...prev,
      isProcessing: true,
      error: null,
      validationError: null,
      needsValidation: false,
    }));

    try {
      const response = await receiptService.validateCorrectedReceipt(correctedData);

      setState(prev => ({
        ...prev,
        isProcessing: false,
        processedData: response.processed_data || null,
        extractedData: response.processed_data || null,
        needsValidation: false, // Validation passed, no need to show modal again
        validationError: null,
      }));

      console.log('[useReceiptOCR] Corrected data validated successfully');

      return response;
    } catch (error) {
      const apiError = error as ApiError;

      // Check if this is still a validation error
      if (apiError.status === 422) {
        const errorDetails = apiError.details?.detail || apiError.details;

        setState(prev => ({
          ...prev,
          isProcessing: false,
          validationError: errorDetails || apiError.message,
          extractedData: correctedData, // Keep the user's corrected data
          needsValidation: true,
        }));
      } else {
        setState(prev => ({
          ...prev,
          isProcessing: false,
          error: apiError.message || 'Failed to validate receipt',
        }));
      }
      throw error;
    }
  }, []);


  const reset = useCallback(() => {
    setState({
      isUploading: false,
      isProcessing: false,
      uploadProgress: 0,
      receiptId: null,
      rawText: null,
      processedData: null,
      extractedData: null,
      error: null,
      validationError: null,
      needsValidation: false,
    });
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
    }));
  }, []);

  return {
    state,
    actions: {
      uploadAndProcessReceipt,
      validateCorrectedData,
      reset,
      clearError,
    },
  };
};