import apiClient from './api';
import { ReceiptProcessResponse } from '@/types/bill.types';

export class ReceiptService {
  /**
   * Upload and process receipt in a single stateless call.
   * Backend processes: Upload → OCR → AI Extraction → Validation
   */
  async processReceipt(file: File, onProgress?: (progress: number) => void): Promise<ReceiptProcessResponse> {
    return apiClient.upload('/receipt/process', file, onProgress);
  }

  /**
   * Validate user-corrected receipt data.
   * Use this after the user has corrected extraction errors.
   */
  async validateCorrectedReceipt(correctedData: any): Promise<ReceiptProcessResponse> {
    return apiClient.post('/receipt/validate', correctedData);
  }
}

export const receiptService = new ReceiptService();
