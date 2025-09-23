import { useState, useCallback } from 'react';
import { ReceiptData } from '@/types/bill.types';

interface ValidationModalState {
  isOpen: boolean;
  imageUrl: string | null;
  extractedData: any | null;
  validationErrors: any | null;
  ocrText: string | null;
  hasValidatedData: boolean;
}

export const useValidationModal = () => {
  const [state, setState] = useState<ValidationModalState>({
    isOpen: false,
    imageUrl: null,
    extractedData: null,
    validationErrors: null,
    ocrText: null,
    hasValidatedData: false,
  });

  const openModal = useCallback((
    imageUrl: string,
    extractedData: any,
    validationErrors: any = null,
    ocrText: string | null = null
  ) => {
    console.log('[useValidationModal] Opening validation modal');
    setState({
      isOpen: true,
      imageUrl,
      extractedData,
      validationErrors,
      ocrText,
      hasValidatedData: false,
    });
  }, []);

  const closeModal = useCallback(() => {
    console.log('[useValidationModal] Closing validation modal');
    setState(prev => ({
      ...prev,
      isOpen: false,
    }));
  }, []);

  const markAsValidated = useCallback((validatedData: any) => {
    console.log('[useValidationModal] Marking data as validated');
    setState(prev => ({
      ...prev,
      extractedData: validatedData,
      hasValidatedData: true,
    }));
  }, []);

  const canReopenModal = useCallback(() => {
    return state.imageUrl !== null && state.extractedData !== null;
  }, [state.imageUrl, state.extractedData]);

  const reopenModal = useCallback(() => {
    if (canReopenModal()) {
      console.log('[useValidationModal] Reopening validation modal');
      setState(prev => ({
        ...prev,
        isOpen: true,
      }));
    }
  }, [canReopenModal]);

  const reset = useCallback(() => {
    console.log('[useValidationModal] Resetting validation modal state');
    setState({
      isOpen: false,
      imageUrl: null,
      extractedData: null,
      validationErrors: null,
      ocrText: null,
      hasValidatedData: false,
    });
  }, []);

  const updateExtractedData = useCallback((newData: any) => {
    setState(prev => ({
      ...prev,
      extractedData: newData,
    }));
  }, []);

  return {
    state,
    actions: {
      openModal,
      closeModal,
      markAsValidated,
      canReopenModal,
      reopenModal,
      reset,
      updateExtractedData,
    },
  };
};
