// frontend/src/hooks/useSession.ts
import { useState, useEffect, useCallback } from 'react';
import { sessionService, SessionData, UpdateSessionData } from '@/services/sessionService';
import { Person } from '@/types/person.types';
import { BillItem, ReceiptData } from '@/types/bill.types';
import { PersonSplit } from '@/types/split.types';

export interface SessionState {
  sessionToken: string | null;
  sessionData: SessionData | null;
  isLoading: boolean;
  error: string | null;
  isInitialized: boolean;
  hasExistingSession: boolean;
}

export const useSession = () => {
  const [state, setState] = useState<SessionState>({
    sessionToken: null,
    sessionData: null,
    isLoading: false,
    error: null,
    isInitialized: true, // Start as initialized to not block UI
    hasExistingSession: false,
  });

  // Initialize session on mount (non-blocking)
  useEffect(() => {
    // Check for existing token and try to load session data
    const existingToken = sessionService.getSessionToken();
    if (existingToken) {
      console.log('Found existing session token, loading session data...');
      setState(prev => ({
        ...prev,
        sessionToken: existingToken,
        hasExistingSession: true,
        isLoading: true,
      }));
      
      // Try to load the session data
      sessionService.getSession(existingToken)
        .then(response => {
          if (response.success) {
            console.log('Session data loaded successfully');
            setState(prev => ({
              ...prev,
              sessionData: response.data,
              isLoading: false,
            }));
          } else {
            console.log('Failed to load session data, will create new session');
            setState(prev => ({
              ...prev,
              hasExistingSession: false,
              isLoading: false,
            }));
          }
        })
        .catch(error => {
          console.error('Error loading session:', error);
          setState(prev => ({
            ...prev,
            hasExistingSession: false,
            isLoading: false,
            error: null, // Don't show error - just continue without session
          }));
        });
    }
  }, []);

  // Remove this function entirely - it's causing circular dependency

  const createNewSession = useCallback(async () => {
    console.log('Creating new session...');
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Session creation timeout')), 5000)
      );
      
      const response = await Promise.race([
        sessionService.createSession(),
        timeoutPromise
      ]) as any;
      
      console.log('Create session response:', response);
      
      if (response.success) {
        const { session_token } = response.data;
        sessionService.saveSessionToken(session_token);
        console.log('Session token saved:', session_token);
        
        // Get the full session data with timeout
        const sessionResponse = await Promise.race([
          sessionService.getSession(session_token),
          timeoutPromise
        ]) as any;
        
        console.log('Session data retrieved:', sessionResponse);
        
        setState(prev => ({
          ...prev,
          sessionToken: session_token,
          sessionData: sessionResponse.data,
          hasExistingSession: false,
          isInitialized: true,
          isLoading: false,
        }));
        console.log('Session initialized successfully');
      }
    } catch (error) {
      console.error('Failed to create new session:', error);
      setState(prev => ({
        ...prev,
        error: 'Session unavailable - app will work without persistence',
        isLoading: false,
        isInitialized: true,
      }));
    }
  }, []);

  const updateSession = useCallback(async (data: UpdateSessionData) => {
    if (!state.sessionToken) {
      console.log('No session token, skipping update');
      return false;
    }

    try {
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Session update timeout')), 3000)
      );
      
      const response = await Promise.race([
        sessionService.updateSession(state.sessionToken, data),
        timeoutPromise
      ]) as any;
      
      if (response.success) {
        // Update local session data immediately
        setState(prev => ({
          ...prev,
          sessionData: prev.sessionData ? {
            ...prev.sessionData,
            ...data,
            updated_at: new Date().toISOString(),
          } : null,
        }));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to update session (continuing anyway):', error);
      // Don't set error state - just continue without session
      return false;
    }
  }, [state.sessionToken]);

  const clearSession = useCallback(async () => {
    if (state.sessionToken) {
      try {
        await sessionService.deleteSession(state.sessionToken);
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
    
    sessionService.removeSessionToken();
    setState({
      sessionToken: null,
      sessionData: null,
      isLoading: false,
      error: null,
      isInitialized: true,
      hasExistingSession: false,
    });
  }, [state.sessionToken]);

  const restoreSession = useCallback(async () => {
    if (state.hasExistingSession && state.sessionData) {
      return {
        currentStep: state.sessionData.current_step,
        participants: state.sessionData.participants,
        receiptData: state.sessionData.receipt_data,
        receiptId: state.sessionData.receipt_id,
        itemAssignments: state.sessionData.item_assignments,
        splitResults: state.sessionData.split_results,
      };
    }
    return null;
  }, [state.hasExistingSession, state.sessionData]);

  // Auto-save helpers with improved error handling
  const saveStep = useCallback(async (step: number) => {
    if (!state.sessionToken) return false;
    try {
      return await updateSession({ current_step: step });
    } catch (error) {
      console.error('Failed to save step:', error);
      return false;
    }
  }, [state.sessionToken, updateSession]);

  const saveParticipants = useCallback(async (participants: Person[]) => {
    if (!state.sessionToken) return false;
    try {
      // Update both current participants and known participants
      const currentKnown = state.sessionData?.known_participants || [];
      const allKnownParticipants = [...currentKnown];
      
      // Only add participants with valid names to known list (avoid duplicates by id and name)
      participants.forEach(participant => {
        // Skip participants with empty or invalid names
        if (!participant.name || !participant.name.trim()) {
          return;
        }
        
        // Check if already exists by id or by name (case insensitive)
        const existsByIdOrName = allKnownParticipants.some(known => 
          known.id === participant.id || 
          known.name.trim().toLowerCase() === participant.name.trim().toLowerCase()
        );
        
        if (!existsByIdOrName) {
          allKnownParticipants.push(participant);
        }
      });
      
      return await updateSession({ 
        participants, 
        known_participants: allKnownParticipants 
      });
    } catch (error) {
      console.error('Failed to save participants:', error);
      return false;
    }
  }, [state.sessionToken, state.sessionData, updateSession]);

  const saveReceiptData = useCallback(async (receiptData: ReceiptData, receiptId: string) => {
    if (!state.sessionToken) return false;
    try {
      return await updateSession({ receipt_data: receiptData, receipt_id: receiptId });
    } catch (error) {
      console.error('Failed to save receipt data:', error);
      return false;
    }
  }, [state.sessionToken, updateSession]);

  const saveItemAssignments = useCallback(async (itemAssignments: Array<{ item: BillItem; assignedTo: string | null }>) => {
    if (!state.sessionToken) return false;
    try {
      return await updateSession({ item_assignments: itemAssignments });
    } catch (error) {
      console.error('Failed to save item assignments:', error);
      return false;
    }
  }, [state.sessionToken, updateSession]);

  const saveSplitResults = useCallback(async (splitResults: PersonSplit[]) => {
    if (!state.sessionToken) return false;
    try {
      return await updateSession({ split_results: splitResults });
    } catch (error) {
      console.error('Failed to save split results:', error);
      return false;
    }
  }, [state.sessionToken, updateSession]);

  const getKnownParticipants = useCallback(() => {
    const knownParticipants = state.sessionData?.known_participants || [];
    // Filter out any participants with empty or invalid names
    return knownParticipants.filter(participant => 
      participant.name && participant.name.trim().length > 0
    );
  }, [state.sessionData]);

  return {
    state,
    actions: {
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
    },
  };
};
