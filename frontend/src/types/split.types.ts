export interface SplitCalculation {
  bill_id: string;
  participants: string[];
  person_splits: PersonSplit[];
  total_bill: number;
  total_tax: number;
  total_service_charge: number;
  total_discount: number;
  calculation_method: string;
}

export interface PersonSplit {
  person_id: string;
  person_name: string;
  items: BillItem[];
  subtotal: number;
  tax_share: number;
  service_charge_share: number;
  discount_share: number;
  total: number;
}

export interface BillItem {
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number; // Changed from 'total' to 'total_price' for consistency
}

export interface SplitCalculationRequest {
  bill_id: string;
  participants: string[];
  calculation_method?: string;
}

export interface SplitCalculationResponse {
  success: boolean;
  message: string;
  calculation?: {
    split_id: string;
    bill_id: string;
    participants: string[];
    person_splits: PersonSplit[];
    totals: {
      total_bill: number;
      total_tax: number;
      total_service_charge: number;
      total_discount: number;
    };
    calculation_method: string;
  };
}
