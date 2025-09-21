import apiClient from './api';
import { ReceiptUploadResponse, ReceiptProcessResponse, ReceiptData } from '@/types/bill.types';

export class ReceiptService {
  async uploadReceipt(file: File, onProgress?: (progress: number) => void): Promise<ReceiptUploadResponse> {
    return apiClient.upload('/receipt/upload', file, onProgress);
  }

  async processReceipt(receiptId: string): Promise<ReceiptProcessResponse> {
    return apiClient.post(`/receipt/process/${receiptId}`);
  }

  async reprocessReceipt(receiptId: string, correctedData: any): Promise<ReceiptProcessResponse> {
    return apiClient.post(`/receipt/reprocess/${receiptId}`, correctedData);
  }

  async getReceipt(receiptId: string): Promise<{
    id: string;
    filename: string;
    raw_text: string;
    processed_data?: ReceiptData;
    created_at: string;
    updated_at: string;
  }> {
    return apiClient.get(`/receipt/${receiptId}`);
  }

  async deleteReceipt(receiptId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete(`/receipt/${receiptId}`);
  }
}

export const receiptService = new ReceiptService();