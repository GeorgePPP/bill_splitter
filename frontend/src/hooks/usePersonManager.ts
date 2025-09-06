import { useState, useCallback } from 'react';
import { Person } from '@/types/person.types';
import { validateName, validateEmail, validatePhone } from '@/utils/validators';

export interface PersonManagerState {
  participants: Person[];
  currentPerson: Person | null;
  isEditing: boolean;
  error: string | null;
}

export const usePersonManager = () => {
  const [state, setState] = useState<PersonManagerState>({
    participants: [],
    currentPerson: null,
    isEditing: false,
    error: null,
  });

  const addPerson = useCallback((person: Omit<Person, 'id'>) => {
    // Validate person data
    if (!validateName(person.name)) {
      setState(prev => ({
        ...prev,
        error: 'Please enter a valid name (at least 2 characters, letters only)',
      }));
      return false;
    }

    if (person.email && !validateEmail(person.email)) {
      setState(prev => ({
        ...prev,
        error: 'Please enter a valid email address',
      }));
      return false;
    }

    if (person.phone && !validatePhone(person.phone)) {
      setState(prev => ({
        ...prev,
        error: 'Please enter a valid phone number',
      }));
      return false;
    }

    const newPerson: Person = {
      ...person,
      id: `person_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };

    setState(prev => ({
      ...prev,
      participants: [...prev.participants, newPerson],
      error: null,
    }));

    return true;
  }, []);

  const updatePerson = useCallback((id: string, updates: Partial<Person>) => {
    // Validate updated data
    if (updates.name && !validateName(updates.name)) {
      setState(prev => ({
        ...prev,
        error: 'Please enter a valid name (at least 2 characters, letters only)',
      }));
      return false;
    }

    if (updates.email && !validateEmail(updates.email)) {
      setState(prev => ({
        ...prev,
        error: 'Please enter a valid email address',
      }));
      return false;
    }

    if (updates.phone && !validatePhone(updates.phone)) {
      setState(prev => ({
        ...prev,
        error: 'Please enter a valid phone number',
      }));
      return false;
    }

    setState(prev => ({
      ...prev,
      participants: prev.participants.map(person =>
        person.id === id ? { ...person, ...updates } : person
      ),
      error: null,
    }));

    return true;
  }, []);

  const removePerson = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      participants: prev.participants.filter(person => person.id !== id),
      error: null,
    }));
  }, []);

  const getPerson = useCallback((id: string) => {
    return state.participants.find(person => person.id === id) || null;
  }, [state.participants]);

  const setCurrentPerson = useCallback((person: Person | null) => {
    setState(prev => ({
      ...prev,
      currentPerson: person,
      isEditing: person !== null,
    }));
  }, []);

  const startEditing = useCallback((person: Person) => {
    setState(prev => ({
      ...prev,
      currentPerson: person,
      isEditing: true,
    }));
  }, []);

  const stopEditing = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentPerson: null,
      isEditing: false,
    }));
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      participants: [],
      currentPerson: null,
      isEditing: false,
      error: null,
    });
  }, []);

  const canAddMore = useCallback((maxCount: number) => {
    return state.participants.length < maxCount;
  }, [state.participants.length]);

  const isPersonValid = useCallback((person: Partial<Person>) => {
    if (!person.name || !validateName(person.name)) return false;
    if (person.email && !validateEmail(person.email)) return false;
    if (person.phone && !validatePhone(person.phone)) return false;
    return true;
  }, []);

  return {
    state,
    actions: {
      addPerson,
      updatePerson,
      removePerson,
      getPerson,
      setCurrentPerson,
      startEditing,
      stopEditing,
      clearError,
      reset,
      canAddMore,
      isPersonValid,
    },
  };
};
