export interface Person {
  id: string;
  name: string;
  email?: string;
  phone?: string;
}

export interface PersonAssignment {
  person_id: string;
  person_name: string;
  assigned_items: string[];
  subtotal: number;
  tax_share: number;
  total: number;
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
  total: number;
}
