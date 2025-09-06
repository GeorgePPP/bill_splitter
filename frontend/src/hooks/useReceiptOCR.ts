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
  error: string | null;
}

export const useReceiptOCR = () => {
  const [state, setState] = useState<ReceiptOCRState>({
    isUploading: false,
    isProcessing: false,
    uploadProgress: 0,
    receiptId: null,
    rawText: null,
    processedData: null,
    error: null,
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
    }));

    try {
      const response = await receiptService.processReceipt(receiptId);

      setState(prev => ({
        ...prev,
        isProcessing: false,
        processedData: response.processed_data || null,
      }));

      return response;
    } catch (error) {
      const apiError = error as ApiError;
      setState(prev => ({
        ...prev,
        isProcessing: false,
        error: apiError.message || 'Failed to process receipt',
      }));
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
      error: null,
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
      reset,
      clearError,
    },
  };
};
