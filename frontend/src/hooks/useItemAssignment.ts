import { useState, useCallback } from 'react';
import { BillItem } from '@/types/bill.types';
import { Person } from '@/types/person.types';

export interface ItemSplit {
  personId: string;
  amount: number;
  percentage: number;
}

export interface ItemAssignment {
  item: BillItem;
  assignedTo: string | null; // For single assignment (backward compatibility)
  splits: ItemSplit[]; // For multiple assignments
  isMultipleAssignment: boolean;
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
  pendingSplitModal: {
    itemIndex: number;
    personIds: string[];
  } | null;
}

const convertToSessionFormat = (
  assignments: ItemAssignment[]
): Array<{ item: BillItem; assignedTo: string | null }> => {
  return assignments.map(assignment => ({
    item: assignment.item,
    assignedTo: assignment.isMultipleAssignment ? null : assignment.assignedTo,
  }));
};

const isSameItem = (a: BillItem, b: BillItem) => {
  return (
    a.name === b.name &&
    a.quantity === b.quantity &&
    a.unit_price === b.unit_price &&
    a.total_price === b.total_price
  );
};

export const useItemAssignment = (sessionActions?: {
  saveItemAssignments?: (assignments: Array<{ item: BillItem; assignedTo: string | null }>) => void;
}) => {
  const persistAssignments = useCallback((assignments: ItemAssignment[]) => {
    if (sessionActions?.saveItemAssignments) {
      sessionActions.saveItemAssignments(convertToSessionFormat(assignments));
    }
  }, [sessionActions]);

  const [state, setState] = useState<ItemAssignmentState>({
    assignments: [],
    selectedItem: null,
    isAssigning: false,
    error: null,
    pendingAssignment: null,
    pendingSplitModal: null,
  });

  const initializeAssignments = useCallback((
    items: BillItem[],
    savedAssignments?: Array<{ item: BillItem; assignedTo: string | null }>,
    options?: { persist?: boolean }
  ) => {
    setState(prev => {
      const savedAssignmentsCopy = savedAssignments ? [...savedAssignments] : [];
      const assignments = items.map(item => {
        let assignedTo: string | null = null;

        if (savedAssignmentsCopy.length > 0) {
          const matchIndex = savedAssignmentsCopy.findIndex(saved =>
            isSameItem(saved.item, item)
          );

          if (matchIndex !== -1) {
            assignedTo = savedAssignmentsCopy[matchIndex].assignedTo || null;
            savedAssignmentsCopy.splice(matchIndex, 1);
          }
        }

        return {
          item,
          assignedTo,
          splits: [],
          isMultipleAssignment: false,
        };
      });

      if (options?.persist !== false) {
        persistAssignments(assignments);
      }

      return {
        ...prev,
        assignments,
        error: null,
        pendingAssignment: null,
        pendingSplitModal: null,
      };
    });
  }, [persistAssignments]);

  const checkForDuplicateAssignment = useCallback((itemIndex: number, personId: string, participants: Person[]) => {
    const itemToAssign = state.assignments[itemIndex];
    if (!itemToAssign) return null;

    // For multiple assignments, check if person is already in splits
    if (itemToAssign.isMultipleAssignment) {
      const existingInSplits = itemToAssign.splits.some(split => split.personId === personId);
      if (existingInSplits) {
        const person = participants.find(p => p.id === personId);
        return {
          itemName: itemToAssign.item.name,
          personId,
          personName: person?.name || 'Unknown',
          existingCount: 1,
          newCount: 2,
        };
      }
    }

    // For single assignments, check other items with same name
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
    const assignment = state.assignments[itemIndex];
    if (!assignment) return { requiresConfirmation: false, duplicateInfo: null };

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

    // Proceed with single assignment
    setState(prev => {
      const newAssignments = prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? { 
              ...assignment, 
              assignedTo: personId,
              splits: [],
              isMultipleAssignment: false,
            }
          : assignment
      );
      persistAssignments(newAssignments);
      return {
        ...prev,
        assignments: newAssignments,
        error: null,
        pendingAssignment: null,
      };
    });
    
    return { requiresConfirmation: false, duplicateInfo: null };
  }, [checkForDuplicateAssignment, state.assignments, persistAssignments]);

  const assignItemToMultiplePeople = useCallback((itemIndex: number, personIds: string[], splitType: 'equal' | 'unequal' = 'equal', customSplits?: ItemSplit[], forceCustomSplit?: boolean) => {
    const assignment = state.assignments[itemIndex];
    if (!assignment) return;

    // If only one person is selected, do a single assignment
    if (personIds.length === 1) {
      setState(prev => {
        const newAssignments = prev.assignments.map((assignment, index) =>
          index === itemIndex
            ? { 
                ...assignment, 
                assignedTo: personIds[0],
                splits: [],
                isMultipleAssignment: false,
              }
            : assignment
        );
        persistAssignments(newAssignments);
        return {
          ...prev,
          assignments: newAssignments,
          pendingSplitModal: null,
          error: null,
        };
      });
      return;
    }

    // If forceCustomSplit is true, always open the modal for user to choose
    if (forceCustomSplit || (!customSplits && splitType === 'unequal')) {
      setState(prev => ({
        ...prev,
        pendingSplitModal: {
          itemIndex,
          personIds,
        },
        error: null,
      }));
      return;
    }

    let splits: ItemSplit[];

    if (customSplits) {
      // Use provided custom splits
      splits = customSplits;
    } else {
      // Default to equal split
      const equalAmount = assignment.item.total_price / personIds.length;
      const equalPercentage = 100 / personIds.length;
      
      splits = personIds.map(personId => ({
        personId,
        amount: Math.round(equalAmount * 100) / 100,
        percentage: Math.round(equalPercentage * 100) / 100,
      }));

      // Adjust for rounding differences
      const totalAssigned = splits.reduce((sum, split) => sum + split.amount, 0);
      const difference = assignment.item.total_price - totalAssigned;
      if (Math.abs(difference) > 0.01) {
        splits[0].amount += difference;
        splits[0].amount = Math.round(splits[0].amount * 100) / 100;
      }
    }

    setState(prev => {
      const newAssignments = prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? {
              ...assignment,
              assignedTo: null,
              splits,
              isMultipleAssignment: true,
            }
          : assignment
      );
      persistAssignments(newAssignments);
      return {
        ...prev,
        assignments: newAssignments,
        pendingSplitModal: null,
        error: null,
      };
    });
  }, [state.assignments, persistAssignments]);

  const unassignItem = useCallback((itemIndex: number) => {
    setState(prev => {
      const newAssignments = prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? { 
              ...assignment, 
              assignedTo: null,
              splits: [],
              isMultipleAssignment: false,
            }
          : assignment
      );
      persistAssignments(newAssignments);
      return {
        ...prev,
        assignments: newAssignments,
        error: null,
      };
    });
  }, [persistAssignments]);

  const removePersonFromSplit = useCallback((itemIndex: number, personId: string) => {
    setState(prev => {
      const newAssignments = prev.assignments.map((assignment, index) => {
        if (index !== itemIndex) return assignment;

        const updatedSplits = assignment.splits.filter(split => split.personId !== personId);
        
        if (updatedSplits.length === 0) {
          return {
            ...assignment,
            assignedTo: null,
            splits: [],
            isMultipleAssignment: false,
          };
        } else if (updatedSplits.length === 1) {
          return {
            ...assignment,
            assignedTo: updatedSplits[0].personId,
            splits: [],
            isMultipleAssignment: false,
          };
        } else {
          // Redistribute amounts proportionally
          const remainingTotal = updatedSplits.reduce((sum, split) => sum + split.amount, 0);
          const scaleFactor = assignment.item.total_price / remainingTotal;
          
          const redistributedSplits = updatedSplits.map(split => ({
            ...split,
            amount: Math.round(split.amount * scaleFactor * 100) / 100,
            percentage: Math.round((split.amount * scaleFactor / assignment.item.total_price) * 100 * 100) / 100,
          }));

          return {
            ...assignment,
            splits: redistributedSplits,
          };
        }
      });

      persistAssignments(newAssignments);

      return {
        ...prev,
        assignments: newAssignments,
        error: null,
      };
    });
  }, [persistAssignments]);

  const updateSplitAmount = useCallback((itemIndex: number, personId: string, amount: number) => {
    setState(prev => {
      const newAssignments = prev.assignments.map((assignment, index) => {
        if (index !== itemIndex) return assignment;

        const updatedSplits = assignment.splits.map(split => 
          split.personId === personId 
            ? {
                ...split,
                amount: Math.round(amount * 100) / 100,
                percentage: Math.round((amount / assignment.item.total_price) * 100 * 100) / 100,
              }
            : split
        );

        return {
          ...assignment,
          splits: updatedSplits,
        };
      });

      persistAssignments(newAssignments);

      return {
        ...prev,
        assignments: newAssignments,
        error: null,
      };
    });
  }, [persistAssignments]);

  const reassignItem = useCallback((itemIndex: number, newPersonId: string) => {
    setState(prev => {
      const newAssignments = prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? { 
              ...assignment, 
              assignedTo: newPersonId,
              splits: [],
              isMultipleAssignment: false,
            }
          : assignment
      );

      persistAssignments(newAssignments);

      return {
        ...prev,
        assignments: newAssignments,
        error: null,
      };
    });
  }, [persistAssignments]);

  const selectItem = useCallback((itemIndex: number | null) => {
    setState(prev => ({
      ...prev,
      selectedItem: itemIndex,
    }));
  }, []);

  const getAssignedItems = useCallback((personId: string) => {
    const items: Array<BillItem & { splitAmount?: number }> = [];
    
    state.assignments.forEach(assignment => {
      if (assignment.assignedTo === personId) {
        items.push(assignment.item);
      } else if (assignment.isMultipleAssignment) {
        const split = assignment.splits.find(s => s.personId === personId);
        if (split) {
          items.push({
            ...assignment.item,
            splitAmount: split.amount,
          });
        }
      }
    });

    return items;
  }, [state.assignments]);

  const getUnassignedItems = useCallback(() => {
    return state.assignments
      .filter(assignment => !assignment.assignedTo && !assignment.isMultipleAssignment)
      .map(assignment => assignment.item);
  }, [state.assignments]);

  const getPersonTotal = useCallback((personId: string) => {
    let total = 0;
    
    state.assignments.forEach(assignment => {
      if (assignment.assignedTo === personId) {
        total += assignment.item.total_price;
      } else if (assignment.isMultipleAssignment) {
        const split = assignment.splits.find(s => s.personId === personId);
        if (split) {
          total += split.amount;
        }
      }
    });

    return Math.round(total * 100) / 100;
  }, [state.assignments]);

  const getAllAssignedItems = useCallback(() => {
    return state.assignments
      .filter(assignment => assignment.assignedTo !== null || assignment.isMultipleAssignment)
      .map(assignment => assignment.item);
  }, [state.assignments]);

  const isAllItemsAssigned = useCallback(() => {
    return state.assignments.every(assignment => 
      assignment.assignedTo !== null || assignment.isMultipleAssignment
    );
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
    const unassignedCount = state.assignments.filter(a => 
      !a.assignedTo && !a.isMultipleAssignment
    ).length;
    
    if (unassignedCount > 0) {
      setState(prev => ({
        ...prev,
        error: `${unassignedCount} item(s) are not assigned to anyone`,
      }));
      return false;
    }

    // Validate split totals
    for (const assignment of state.assignments) {
      if (assignment.isMultipleAssignment) {
        const totalSplit = assignment.splits.reduce((sum, split) => sum + split.amount, 0);
        const difference = Math.abs(totalSplit - assignment.item.total_price);
        
        if (difference > 0.01) {
          setState(prev => ({
            ...prev,
            error: `Split amounts for "${assignment.item.name}" don't add up to the item total`,
          }));
          return false;
        }
      }
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
      const newAssignments = prev.assignments.map((assignment, index) =>
        index === itemIndex
          ? { 
              ...assignment, 
              assignedTo: personId,
              splits: [],
              isMultipleAssignment: false,
            }
          : assignment
      );

      persistAssignments(newAssignments);
      
      return {
        ...prev,
        assignments: newAssignments,
        pendingAssignment: null,
        error: null,
      };
    });
  }, [persistAssignments]);

  const cancelPendingAssignment = useCallback(() => {
    setState(prev => ({
      ...prev,
      pendingAssignment: null,
      error: null,
    }));
  }, []);

  const closeSplitModal = useCallback(() => {
    setState(prev => ({
      ...prev,
      pendingSplitModal: null,
    }));
  }, []);

  const reset = useCallback(() => {
    persistAssignments([]);
    setState({
      assignments: [],
      selectedItem: null,
      isAssigning: false,
      error: null,
      pendingAssignment: null,
      pendingSplitModal: null,
    });
  }, [persistAssignments]);

  return {
    state,
    actions: {
      initializeAssignments,
      assignItem,
      assignItemToMultiplePeople,
      unassignItem,
      removePersonFromSplit,
      updateSplitAmount,
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
      checkForDuplicateAssignment,
      confirmPendingAssignment,
      cancelPendingAssignment,
      closeSplitModal,
    },
  };
};
