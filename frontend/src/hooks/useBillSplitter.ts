import { useState, useCallback } from 'react';
import { Person } from '@/types/person.types';
import { BillItem, ReceiptData } from '@/types/bill.types';
import { PersonSplit } from '@/types/split.types';

export interface BillSplitterState {
  // Step 1: Number of people
  numberOfPeople: number;
  
  // Step 2: Participant names
  participants: Person[];
  
  // Step 3: Receipt data
  receiptData: ReceiptData | null;
  receiptId: string | null;
  
  // Step 4: Item assignments
  itemAssignments: Array<{
    item: BillItem;
    assignedTo: string | null;
  }>;
  
  // Step 5: Split results
  splitResults: PersonSplit[] | null;
  
  // UI state
  currentStep: number;
  isLoading: boolean;
  error: string | null;
}

export const useBillSplitter = () => {
  const [state, setState] = useState<BillSplitterState>({
    numberOfPeople: 0,
    participants: [],
    receiptData: null,
    receiptId: null,
    itemAssignments: [],
    splitResults: null,
    currentStep: 1,
    isLoading: false,
    error: null,
  });

  const setNumberOfPeople = useCallback((count: number) => {
    setState(prev => ({
      ...prev,
      numberOfPeople: count,
      participants: prev.participants.slice(0, count),
    }));
  }, []);

  const addParticipant = useCallback((person: Person) => {
    setState(prev => ({
      ...prev,
      participants: [...prev.participants, person],
    }));
  }, []);

  const updateParticipant = useCallback((index: number, person: Person) => {
    setState(prev => ({
      ...prev,
      participants: prev.participants.map((p, i) => i === index ? person : p),
    }));
  }, []);

  const removeParticipant = useCallback((index: number) => {
    setState(prev => ({
      ...prev,
      participants: prev.participants.filter((_, i) => i !== index),
    }));
  }, []);

  const setParticipants = useCallback((participants: Person[]) => {
    setState(prev => ({
      ...prev,
      participants,
    }));
  }, []);

  const setReceiptData = useCallback((receiptData: ReceiptData, receiptId: string) => {
    setState(prev => ({
      ...prev,
      receiptData,
      receiptId,
      itemAssignments: receiptData.items.map(item => ({
        item,
        assignedTo: null,
      })),
    }));
  }, []);

  const assignItem = useCallback((itemIndex: number, personId: string) => {
    setState(prev => ({
      ...prev,
      itemAssignments: prev.itemAssignments.map((assignment, index) => 
        index === itemIndex 
          ? { ...assignment, assignedTo: personId }
          : assignment
      ),
    }));
  }, []);

  const unassignItem = useCallback((itemIndex: number) => {
    setState(prev => ({
      ...prev,
      itemAssignments: prev.itemAssignments.map((assignment, index) => 
        index === itemIndex 
          ? { ...assignment, assignedTo: null }
          : assignment
      ),
    }));
  }, []);

  const setSplitResults = useCallback((results: PersonSplit[]) => {
    setState(prev => ({
      ...prev,
      splitResults: results,
    }));
  }, []);

  const nextStep = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentStep: Math.min(prev.currentStep + 1, 5),
      error: null,
    }));
  }, []);

  const prevStep = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentStep: Math.max(prev.currentStep - 1, 1),
      error: null,
    }));
  }, []);

  const goToStep = useCallback((step: number) => {
    setState(prev => ({
      ...prev,
      currentStep: Math.max(1, Math.min(step, 5)),
      error: null,
    }));
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({
      ...prev,
      isLoading: loading,
    }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({
      ...prev,
      error,
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      numberOfPeople: 0,
      participants: [],
      receiptData: null,
      receiptId: null,
      itemAssignments: [],
      splitResults: null,
      currentStep: 1,
      isLoading: false,
      error: null,
    });
  }, []);

  const canProceedToNextStep = useCallback(() => {
    switch (state.currentStep) {
      case 1:
        return state.participants.length > 0 &&
               state.participants.every(p => p.name.trim() !== '');
      case 2:
        return state.receiptData !== null;
      case 3:
        return state.itemAssignments.every(assignment => assignment.assignedTo !== null);
      case 4:
        return state.splitResults !== null;
      default:
        return false;
    }
  }, [state]);

  return {
    state,
    actions: {
      setNumberOfPeople,
      addParticipant,
      updateParticipant,
      removeParticipant,
      setParticipants,
      setReceiptData,
      assignItem,
      unassignItem,
      setSplitResults,
      nextStep,
      prevStep,
      goToStep,
      setLoading,
      setError,
      reset,
      canProceedToNextStep,
    },
  };
};
