import { useState, useCallback } from 'react';
import { BillItem } from '@/types/bill.types';
import { Person } from '@/types/person.types';

export interface ItemAssignment {
  item: BillItem;
  assignedTo: string | null;
}

export interface DuplicateAssignmentInfo {
  itemName: string;
  personId: string;
  personName: string;
  existingCount: number;
  newCount: number;
}

export interface ItemAssignmentState {
  assignments: ItemAssignment[];
  selectedItem: number | null;
  isAssigning: boolean;
  error: string | null;
  pendingAssignment: {
    itemIndex: number;
    personId: string;
    duplicateInfo: DuplicateAssignmentInfo | null;
  } | null;
}

export const useItemAssignment = () => {
  const [state, setState] = useState<ItemAssignmentState>({
    assignments: [],
    selectedItem: null,
    isAssigning: false,
    error: null,
    pendingAssignment: null,
  });

  const initializeAssignments = useCallback((items: BillItem[]) => {
    setState(prev => ({
      ...prev,
      assignments: items.map(item => ({
        item,
        assignedTo: null,
      })),
      error: null,
    }));
  }, []);

  const checkForDuplicateAssignment = useCallback((itemIndex: number, personId: string, participants: Person[]) => {
    const itemToAssign = state.assignments[itemIndex];
    if (!itemToAssign) return null;

    // Count how many times this item name is already assigned to this person
    const existingCount = state.assignments.filter(assignment => 
      assignment.assignedTo === personId && 
      assignment.item.name.toLowerCase().trim() === itemToAssign.item.name.toLowerCase().trim()
    ).length;

    if (existingCount > 0) {
      const person = participants.find(p => p.id === personId);
      return {
        itemName: itemToAssign.item.name,
        personId,
        personName: person?.name || 'Unknown',
        existingCount,
        newCount: existingCount + 1,
      };
    }

    return null;
  }, [state.assignments]);

  const assignItem = useCallback((itemIndex: number, personId: string, participants?: Person[]) => {
    // Check for duplicate assignment if participants are provided
    if (participants) {
      const duplicateInfo = checkForDuplicateAssignment(itemIndex, personId, participants);
      
      if (duplicateInfo) {
        // Set pending assignment for confirmation
        setState(prev => ({
          ...prev,
          pendingAssignment: {
            itemIndex,
            personId,
            duplicateInfo,
          },
          error: null,
        }));
        return { requiresConfirmation: true, duplicateInfo };
      }
    }

    // Proceed with assignment
    setState(prev => ({
      ...prev,
      assignments: prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? { ...assignment, assignedTo: personId }
          : assignment
      ),
      error: null,
      pendingAssignment: null,
    }));
    
    return { requiresConfirmation: false, duplicateInfo: null };
  }, [checkForDuplicateAssignment]);

  const unassignItem = useCallback((itemIndex: number) => {
    setState(prev => ({
      ...prev,
      assignments: prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? { ...assignment, assignedTo: null }
          : assignment
      ),
      error: null,
    }));
  }, []);

  const reassignItem = useCallback((itemIndex: number, newPersonId: string) => {
    setState(prev => ({
      ...prev,
      assignments: prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? { ...assignment, assignedTo: newPersonId }
          : assignment
      ),
      error: null,
    }));
  }, []);

  const selectItem = useCallback((itemIndex: number | null) => {
    setState(prev => ({
      ...prev,
      selectedItem: itemIndex,
    }));
  }, []);

  const getAssignedItems = useCallback((personId: string) => {
    return state.assignments
      .filter(assignment => assignment.assignedTo === personId)
      .map(assignment => assignment.item);
  }, [state.assignments]);

  const getUnassignedItems = useCallback(() => {
    return state.assignments
      .filter(assignment => assignment.assignedTo === null)
      .map(assignment => assignment.item);
  }, [state.assignments]);

  const getPersonTotal = useCallback((personId: string) => {
    return state.assignments
      .filter(assignment => assignment.assignedTo === personId)
      .reduce((total, assignment) => total + assignment.item.total, 0);
  }, [state.assignments]);

  const getAllAssignedItems = useCallback(() => {
    return state.assignments
      .filter(assignment => assignment.assignedTo !== null)
      .map(assignment => assignment.item);
  }, [state.assignments]);

  const isAllItemsAssigned = useCallback(() => {
    return state.assignments.every(assignment => assignment.assignedTo !== null);
  }, [state.assignments]);

  const getAssignmentSummary = useCallback((participants: Person[]) => {
    return participants.map(person => ({
      person,
      assignedItems: getAssignedItems(person.id),
      total: getPersonTotal(person.id),
      itemCount: getAssignedItems(person.id).length,
    }));
  }, [getAssignedItems, getPersonTotal]);

  const validateAssignments = useCallback(() => {
    const unassignedCount = state.assignments.filter(a => a.assignedTo === null).length;
    
    if (unassignedCount > 0) {
      setState(prev => ({
        ...prev,
        error: `${unassignedCount} item(s) are not assigned to anyone`,
      }));
      return false;
    }

    setState(prev => ({
      ...prev,
      error: null,
    }));
    return true;
  }, [state.assignments]);

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
    }));
  }, []);

  const confirmPendingAssignment = useCallback(() => {
    setState(prev => {
      if (!prev.pendingAssignment) return prev;

      const { itemIndex, personId } = prev.pendingAssignment;
      
      return {
        ...prev,
        assignments: prev.assignments.map((assignment, index) =>
          index === itemIndex
            ? { ...assignment, assignedTo: personId }
            : assignment
        ),
        pendingAssignment: null,
        error: null,
      };
    });
  }, []);

  const cancelPendingAssignment = useCallback(() => {
    setState(prev => ({
      ...prev,
      pendingAssignment: null,
      error: null,
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      assignments: [],
      selectedItem: null,
      isAssigning: false,
      error: null,
      pendingAssignment: null,
    });
  }, []);

  const bulkAssign = useCallback((personId: string, itemIndices: number[]) => {
    setState(prev => ({
      ...prev,
      assignments: prev.assignments.map((assignment, index) =>
        itemIndices.includes(index)
          ? { ...assignment, assignedTo: personId }
          : assignment
      ),
      error: null,
    }));
  }, []);

  const bulkUnassign = useCallback((itemIndices: number[]) => {
    setState(prev => ({
      ...prev,
      assignments: prev.assignments.map((assignment, index) =>
        itemIndices.includes(index)
          ? { ...assignment, assignedTo: null }
          : assignment
      ),
      error: null,
    }));
  }, []);

  return {
    state,
    actions: {
      initializeAssignments,
      assignItem,
      unassignItem,
      reassignItem,
      selectItem,
      getAssignedItems,
      getUnassignedItems,
      getPersonTotal,
      getAllAssignedItems,
      isAllItemsAssigned,
      getAssignmentSummary,
      validateAssignments,
      clearError,
      reset,
      bulkAssign,
      bulkUnassign,
      checkForDuplicateAssignment,
      confirmPendingAssignment,
      cancelPendingAssignment,
    },
  };
};
