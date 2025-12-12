// frontend/src/services/sessionService.ts
/**
 * DEPRECATED: Session management is now fully client-side.
 * This file is kept only for type exports.
 * See useSession.ts for the actual implementation.
 */

import { Person } from '@/types/person.types';
import { BillItem, ReceiptData } from '@/types/bill.types';
import { PersonSplit } from '@/types/split.types';

// Re-export types for backward compatibility
export interface SessionData {
  session_token: string;
  current_step: number;
  participants: Person[];
  receipt_data: ReceiptData | null;
  receipt_id: string | null;
  item_assignments: Array<{ item: BillItem; assignedTo: string | null }>;
  split_results: PersonSplit[] | null;
  known_participants: Person[];
  ocr_text: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface UpdateSessionData {
  current_step?: number;
  participants?: Person[];
  receipt_data?: ReceiptData;
  receipt_id?: string;
  item_assignments?: Array<{ item: BillItem; assignedTo: string | null }>;
  split_results?: PersonSplit[];
  known_participants?: Person[];
  ocr_text?: string;
}

// Deprecated - no longer used
export const sessionService = {
  // These methods are no longer called - session is managed in useSession.ts via localStorage
  getSessionToken: () => null,
  saveSessionToken: (_token: string) => {},
  removeSessionToken: () => {},
  createSession: async () => ({ success: false, data: null }),
  getSession: async (_token: string) => ({ success: false, data: null }),
  updateSession: async (_token: string, _data: UpdateSessionData) => ({ success: false }),
  deleteSession: async (_token: string) => ({ success: false }),
  extendSession: async (_token: string) => ({ success: false }),
};