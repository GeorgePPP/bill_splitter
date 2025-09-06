import apiClient from './api';
import { BillSplit, BillItemAssignment } from '@/types/bill.types';
import { Person } from '@/types/person.types';

export class BillService {
  async createBillSplit(data: {
    receipt_data: any;
    participants: string[];
    item_assignments: BillItemAssignment[];
    tax_distribution?: string;
    service_charge_distribution?: string;
    discount_distribution?: string;
  }): Promise<BillSplit> {
    return apiClient.post('/bill/split', data);
  }

  async getBillSplit(billId: string): Promise<BillSplit> {
    return apiClient.get(`/bill/${billId}`);
  }

  async updateItemAssignments(
    billId: string, 
    assignments: BillItemAssignment[]
  ): Promise<{ success: boolean; message: string }> {
    return apiClient.put(`/bill/${billId}/assignments`, assignments);
  }

  async deleteBillSplit(billId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete(`/bill/${billId}`);
  }
}

export const billService = new BillService();
