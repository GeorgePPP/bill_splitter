// frontend/src/services/sessionService.ts
import { apiClient } from './api';
import { Person } from '@/types/person.types';
import { BillItem, ReceiptData } from '@/types/bill.types';
import { PersonSplit } from '@/types/split.types';

export interface SessionData {
  session_token: string;
  expires_at: string;
  current_step: number;
  participants: Person[];
  receipt_data: ReceiptData | null;
  receipt_id: string | null;
  item_assignments: Array<{
    item: BillItem;
    assignedTo: string | null;
  }>;
  split_results: PersonSplit[] | null;
  known_participants: Person[];
  created_at: string;
  updated_at: string;
}

export interface CreateSessionResponse {
  success: boolean;
  data: {
    session_token: string;
    expires_at: string;
    created: boolean;
  };
}

export interface GetSessionResponse {
  success: boolean;
  data: SessionData;
}

export interface UpdateSessionData {
  current_step?: number;
  participants?: Person[];
  receipt_data?: ReceiptData | null;
  receipt_id?: string | null;
  item_assignments?: Array<{
    item: BillItem;
    assignedTo: string | null;
  }>;
  split_results?: PersonSplit[] | null;
  known_participants?: Person[];
}

class SessionService {
  async createSession(userId?: string): Promise<CreateSessionResponse> {
    return apiClient.post('/session/create', { user_id: userId });
  }

  async getSession(sessionToken: string): Promise<GetSessionResponse> {
    return apiClient.get(`/session/${sessionToken}`);
  }

  async updateSession(sessionToken: string, data: UpdateSessionData): Promise<{ success: boolean; message: string }> {
    return apiClient.put(`/session/${sessionToken}`, data);
  }

  async deleteSession(sessionToken: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete(`/session/${sessionToken}`);
  }

  // Local storage helpers
  saveSessionToken(token: string): void {
    localStorage.setItem('bill_splitter_session_token', token);
  }

  getSessionToken(): string | null {
    return localStorage.getItem('bill_splitter_session_token');
  }

  removeSessionToken(): void {
    localStorage.removeItem('bill_splitter_session_token');
  }

  isSessionExpired(expiresAt: string): boolean {
    const expiry = new Date(expiresAt);
    const now = new Date();
    return now >= expiry;
  }

}

export const sessionService = new SessionService();
export default sessionService;
