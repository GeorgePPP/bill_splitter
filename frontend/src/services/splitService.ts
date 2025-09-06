import apiClient from './api';
import { SplitCalculationRequest, SplitCalculationResponse } from '@/types/split.types';

export class SplitService {
  async calculateSplit(request: SplitCalculationRequest): Promise<SplitCalculationResponse> {
    return apiClient.post('/split/calculate', request);
  }

  async getSplitCalculation(splitId: string): Promise<{
    split_id: string;
    bill_id: string;
    participants: string[];
    person_splits: any[];
    totals: {
      total_bill: number;
      total_tax: number;
      total_service_charge: number;
      total_discount: number;
    };
    calculation_method: string;
  }> {
    return apiClient.get(`/split/${splitId}`);
  }

  async listSplitCalculations(): Promise<{
    calculations: Array<{
      split_id: string;
      bill_id: string;
      participants: string[];
      total_bill: number;
      calculation_method: string;
    }>;
    total: number;
  }> {
    return apiClient.get('/split/');
  }

  async deleteSplitCalculation(splitId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete(`/split/${splitId}`);
  }
}

export const splitService = new SplitService();
