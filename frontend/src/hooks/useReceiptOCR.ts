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

  const uploadReceipt = useCallback(async (file: File) => {
    setState(prev => ({
      ...prev,
      isUploading: true,
      uploadProgress: 0,
      error: null,
    }));

    try {
      const response = await receiptService.uploadReceipt(
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
        uploadProgress: 100,
        receiptId: response.receipt_id || null,
        rawText: response.raw_text || null,
      }));

      return response;
    } catch (error) {
      const apiError = error as ApiError;
      setState(prev => ({
        ...prev,
        isUploading: false,
        uploadProgress: 0,
        error: apiError.message || 'Failed to upload receipt',
      }));
      throw error;
    }
  }, []);

  const processReceipt = useCallback(async (receiptId: string) => {
    setState(prev => ({
      ...prev,
      isProcessing: true,
      error: null,
      validationError: null,
      needsValidation: false,
    }));

    try {
      const response = await receiptService.processReceipt(receiptId);

      setState(prev => ({
        ...prev,
        isProcessing: false,
        processedData: response.processed_data || null,
        extractedData: response.processed_data || null,
      }));

      return response;
    } catch (error) {
      const apiError = error as ApiError;
      
      // Check if this is a validation error (422)
      if (apiError.status === 422) {
        // Extract the data from error details
        const extractedData = apiError.details?.extracted_data;
        
        setState(prev => ({
          ...prev,
          isProcessing: false,
          validationError: apiError.details || apiError.message,
          extractedData: extractedData || null,
          needsValidation: true,
        }));
      } else {
        setState(prev => ({
          ...prev,
          isProcessing: false,
          error: apiError.message || 'Failed to process receipt',
        }));
      }
      throw error;
    }
  }, []);

  const reprocessWithCorrectedData = useCallback(async (receiptId: string, correctedData: any) => {
    setState(prev => ({
      ...prev,
      isProcessing: true,
      error: null,
      validationError: null,
      needsValidation: false,
    }));

    try {
      const response = await receiptService.reprocessReceipt(receiptId, correctedData);

      setState(prev => ({
        ...prev,
        isProcessing: false,
        processedData: response.processed_data || null,
        extractedData: response.processed_data || null,
        needsValidation: false,
      }));

      return response;
    } catch (error) {
      const apiError = error as ApiError;
      
      // Check if this is still a validation error
      if (apiError.status === 422) {
        setState(prev => ({
          ...prev,
          isProcessing: false,
          validationError: apiError.details || apiError.message,
          extractedData: correctedData, // Keep the user's corrected data
          needsValidation: true,
        }));
      } else {
        setState(prev => ({
          ...prev,
          isProcessing: false,
          error: apiError.message || 'Failed to reprocess receipt',
        }));
      }
      throw error;
    }
  }, []);

  const getReceipt = useCallback(async (receiptId: string) => {
    try {
      const response = await receiptService.getReceipt(receiptId);
      
      setState(prev => ({
        ...prev,
        receiptId: response.id,
        rawText: response.raw_text,
        processedData: response.processed_data || null,
        extractedData: response.processed_data || null,
      }));

      return response;
    } catch (error) {
      const apiError = error as ApiError;
      setState(prev => ({
        ...prev,
        error: apiError.message || 'Failed to get receipt',
      }));
      throw error;
    }
  }, []);

  const deleteReceipt = useCallback(async (receiptId: string) => {
    try {
      await receiptService.deleteReceipt(receiptId);
      
      setState(prev => ({
        ...prev,
        receiptId: null,
        rawText: null,
        processedData: null,
        extractedData: null,
      }));
    } catch (error) {
      const apiError = error as ApiError;
      setState(prev => ({
        ...prev,
        error: apiError.message || 'Failed to delete receipt',
      }));
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
      uploadReceipt,
      processReceipt,
      getReceipt,
      deleteReceipt,
      reprocessWithCorrectedData,
      reset,
      clearError,
    },
  };
};