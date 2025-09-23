export interface StoreInfo {
  name: string;
  address?: string;
  phone?: string;
}

export interface BillItem {
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number; // Changed from 'total' to 'total_price'
}

export interface TaxOrCharge {
  name: string;
  amount: number;
  percent?: number;
}

export interface ReceiptData {
  receipt_number: string;
  date: string;
  time: string;
  store: StoreInfo;
  items: BillItem[];
  subtotal: number;
  taxes_or_charges: TaxOrCharge[]; // New field replacing individual tax/service_charge fields
  grand_total: number; // Changed from 'total_amount' to 'grand_total'
  payment_method: string;
  transaction_id?: string;
  notes?: string;
}

export interface BillItemAssignment {
  item_name: string;
  quantity: number;
  unit_price: number;
  total_price: number; // Changed from 'total' to 'total_price'
  assigned_to?: string;
}

export interface BillSplit {
  id: string;
  receipt_data: ReceiptData;
  participants: Person[];
  item_assignments: BillItemAssignment[];
  tax_distribution: string;
  service_charge_distribution: string;
  discount_distribution: string;
  created_at: string;
  updated_at: string;
}

export interface ReceiptUploadResponse {
  success: boolean;
  message: string;
  receipt_id?: string;
  raw_text?: string;
}

export interface ReceiptProcessResponse {
  success: boolean;
  message: string;
  processed_data?: ReceiptData;
  ocr_text?: string;
}
