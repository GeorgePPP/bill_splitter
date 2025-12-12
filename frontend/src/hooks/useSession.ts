// frontend/src/hooks/useSession.ts
/**
 * Client-side session management using React state + localStorage.
 * No backend calls - all state is managed locally.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { Person } from '@/types/person.types';
import { BillItem, ReceiptData } from '@/types/bill.types';
import { PersonSplit } from '@/types/split.types';

// ============================================================================
// Types
// ============================================================================

interface SessionData {
  current_step: number;
  participants: Person[];
  receipt_data: ReceiptData | null;
  receipt_id: string | null;
  item_assignments: Array<{ item: BillItem; assignedTo: string | null }>;
  split_results: PersonSplit[] | null;
  known_participants: Person[];
  ocr_text: string | null;
  updated_at: string;
}

interface UpdateSessionData {
  current_step?: number;
  participants?: Person[];
  receipt_data?: ReceiptData;
  receipt_id?: string;
  item_assignments?: Array<{ item: BillItem; assignedTo: string | null }>;
  split_results?: PersonSplit[];
  known_participants?: Person[];
  ocr_text?: string;
}

export interface SessionState {
  sessionToken: string | null;
  sessionData: SessionData | null;
  isLoading: boolean;
  error: string | null;
  isInitialized: boolean;
  hasExistingSession: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'billsplitter_session';

const DEFAULT_SESSION_DATA: SessionData = {
  current_step: 1,
  participants: [],
  receipt_data: null,
  receipt_id: null,
  item_assignments: [],
  split_results: null,
  known_participants: [],
  ocr_text: null,
  updated_at: new Date().toISOString(),
};

// ============================================================================
// Storage Helpers
// ============================================================================

const loadFromStorage = (): SessionData | null => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Failed to load session from storage:', error);
  }
  return null;
};

const saveToStorage = (data: SessionData): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error('Failed to save session to storage:', error);
  }
};

const clearStorage = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear session storage:', error);
  }
};

// ============================================================================
// Hook
// ============================================================================

export const useSession = () => {
  // Load initial state from localStorage
  const [state, setState] = useState<SessionState>(() => {
    const existingData = loadFromStorage();
    return {
      sessionToken: existingData ? 'local-session' : null,
      sessionData: existingData,
      isLoading: false,
      error: null,
      isInitialized: true, // Always initialized immediately
      hasExistingSession: !!existingData,
    };
  });

  // Persist to localStorage whenever sessionData changes
  useEffect(() => {
    if (state.sessionData) {
      saveToStorage(state.sessionData);
    }
  }, [state.sessionData]);

  // Create new session (just initializes default state)
  const createNewSession = useCallback(async () => {
    console.log('Creating new local session...');
    
    const newSessionData: SessionData = {
      ...DEFAULT_SESSION_DATA,
      updated_at: new Date().toISOString(),
    };
    
    saveToStorage(newSessionData);
    
    setState({
      sessionToken: 'local-session',
      sessionData: newSessionData,
      isLoading: false,
      error: null,
      isInitialized: true,
      hasExistingSession: false,
    });
    
    console.log('Local session created');
  }, []);

  // Update session data
  const updateSession = useCallback(async (data: UpdateSessionData): Promise<boolean> => {
    setState(prev => {
      if (!prev.sessionData) return prev;
      
      const updatedData: SessionData = {
        ...prev.sessionData,
        ...data,
        updated_at: new Date().toISOString(),
      };
      
      // Save synchronously
      saveToStorage(updatedData);
      
      return {
        ...prev,
        sessionData: updatedData,
      };
    });
    
    return true;
  }, []);

  // Clear session
  const clearSession = useCallback(async () => {
    clearStorage();
    
    setState({
      sessionToken: null,
      sessionData: null,
      isLoading: false,
      error: null,
      isInitialized: true,
      hasExistingSession: false,
    });
    
    console.log('Session cleared');
  }, []);

  // Restore session (returns existing data if available)
  const restoreSession = useCallback(async () => {
    if (state.hasExistingSession && state.sessionData) {
      return {
        currentStep: state.sessionData.current_step,
        participants: state.sessionData.participants,
        receiptData: state.sessionData.receipt_data,
        receiptId: state.sessionData.receipt_id,
        itemAssignments: state.sessionData.item_assignments,
        splitResults: state.sessionData.split_results,
        ocrText: state.sessionData.ocr_text,
      };
    }
    return null;
  }, [state.hasExistingSession, state.sessionData]);

  // ============================================================================
  // Convenience Save Methods
  // ============================================================================

  const saveStep = useCallback(async (step: number): Promise<boolean> => {
    return updateSession({ current_step: step });
  }, [updateSession]);

  const saveParticipants = useCallback(async (participants: Person[]): Promise<boolean> => {
    // Update known participants (deduplicated)
    const currentKnown = state.sessionData?.known_participants || [];
    const allKnown = [...currentKnown];
    
    participants.forEach(participant => {
      if (!participant.name?.trim()) return;
      
      const exists = allKnown.some(known =>
        known.id === participant.id ||
        known.name.trim().toLowerCase() === participant.name.trim().toLowerCase()
      );
      
      if (!exists) {
        allKnown.push(participant);
      }
    });
    
    return updateSession({
      participants,
      known_participants: allKnown,
    });
  }, [updateSession, state.sessionData?.known_participants]);

  const saveReceiptData = useCallback(async (
    receiptData: ReceiptData,
    receiptId: string
  ): Promise<boolean> => {
    return updateSession({
      receipt_data: receiptData,
      receipt_id: receiptId,
    });
  }, [updateSession]);

  const saveItemAssignments = useCallback(async (
    itemAssignments: Array<{ item: BillItem; assignedTo: string | null }>
  ): Promise<boolean> => {
    return updateSession({ item_assignments: itemAssignments });
  }, [updateSession]);

  const saveSplitResults = useCallback(async (
    splitResults: PersonSplit[]
  ): Promise<boolean> => {
    return updateSession({ split_results: splitResults });
  }, [updateSession]);

  const saveOcrText = useCallback(async (ocrText: string): Promise<boolean> => {
    console.log('Saving OCR text to local session');
    return updateSession({ ocr_text: ocrText });
  }, [updateSession]);

  // Get known participants (filtered for valid names)
  const getKnownParticipants = useCallback((): Person[] => {
    const known = state.sessionData?.known_participants || [];
    return known.filter(p => p.name?.trim().length > 0);
  }, [state.sessionData?.known_participants]);

  // ============================================================================
  // Return Value
  // ============================================================================

  // Memoize actions to prevent unnecessary re-renders
  const actions = useMemo(() => ({
    createNewSession,
    updateSession,
    clearSession,
    restoreSession,
    getKnownParticipants,
    saveStep,
    saveParticipants,
    saveReceiptData,
    saveItemAssignments,
    saveSplitResults,
    saveOcrText,
  }), [
    createNewSession,
    updateSession,
    clearSession,
    restoreSession,
    getKnownParticipants,
    saveStep,
    saveParticipants,
    saveReceiptData,
    saveItemAssignments,
    saveSplitResults,
    saveOcrText,
  ]);

  return {
    state,
    actions,
  };
};

// Re-export types for backward compatibility
export type { SessionData, UpdateSessionData };