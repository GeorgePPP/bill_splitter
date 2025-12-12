import apiClient from './api';
import { SplitCalculationRequest, SplitCalculationResponse } from '@/types/split.types';

export class SplitService {
  /**
   * Calculate bill split based on item assignments (stateless).
   * All data is passed in the request, no server-side storage.
   */
  async calculateSplit(request: SplitCalculationRequest): Promise<SplitCalculationResponse> {
    return apiClient.post('/split/calculate', request);
  }
}

export const splitService = new SplitService();
