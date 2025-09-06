import { useState, useCallback } from 'react';
import { BillItem } from '@/types/bill.types';
import { Person } from '@/types/person.types';

export interface ItemAssignment {
  item: BillItem;
  assignedTo: string | null;
}

export interface ItemAssignmentState {
  assignments: ItemAssignment[];
  selectedItem: number | null;
  isAssigning: boolean;
  error: string | null;
}

export const useItemAssignment = () => {
  const [state, setState] = useState<ItemAssignmentState>({
    assignments: [],
    selectedItem: null,
    isAssigning: false,
    error: null,
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

  const assignItem = useCallback((itemIndex: number, personId: string) => {
    setState(prev => ({
      ...prev,
      assignments: prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? { ...assignment, assignedTo: personId }
          : assignment
      ),
      error: null,
    }));
  }, []);

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

  const reset = useCallback(() => {
    setState({
      assignments: [],
      selectedItem: null,
      isAssigning: false,
      error: null,
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
    },
  };
};
