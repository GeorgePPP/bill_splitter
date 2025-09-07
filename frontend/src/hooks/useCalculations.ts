import { useState, useCallback, useMemo } from 'react';
import { Person } from '@/types/person.types';
import { PersonSplit } from '@/types/split.types';
import { ItemAssignment } from './useItemAssignment';
import { 
  calculateSubtotal, 
  roundToCents,
  distributeAmount
} from '@/utils/calculations';

export interface CalculationState {
  personSplits: PersonSplit[];
  totalBill: number;
  totalTax: number;
  totalServiceCharge: number;
  totalDiscount: number;
  netTotal: number;
  calculationMethod: 'proportional' | 'equal';
  error: string | null;
}

export const useCalculations = () => {
  const [state, setState] = useState<CalculationState>({
    personSplits: [],
    totalBill: 0,
    totalTax: 0,
    totalServiceCharge: 0,
    totalDiscount: 0,
    netTotal: 0,
    calculationMethod: 'proportional',
    error: null,
  });

  const calculateSplit = useCallback((
    participants: Person[],
    assignments: ItemAssignment[],
    receiptData: {
      subtotal: number;
      taxes_or_charges: Array<{ name: string; amount: number; percent?: number }>;
      grand_total: number; 
    },
    method: 'proportional' | 'equal' = 'proportional'
  ) => {
    try {
      // CRITICAL: The grand_total is the final amount payable - no additional calculations needed
      const finalTotal = receiptData.grand_total;
      
      // Calculate each person's subtotal from assigned items (including split items)
      const personSubtotals = participants.map(person => {
        let subtotal = 0;
        
        assignments.forEach(assignment => {
          if (assignment.assignedTo === person.id) {
            // Single assignment - person gets full item
            subtotal += assignment.item.total_price;
          } else if (assignment.isMultipleAssignment) {
            // Multiple assignment - person gets their split amount
            const split = assignment.splits.find(s => s.personId === person.id);
            if (split) {
              subtotal += split.amount;
            }
          }
        });
        
        return roundToCents(subtotal);
      });

      const totalItemsSubtotal = personSubtotals.reduce((sum, subtotal) => sum + subtotal, 0);
      
      // For backward compatibility, separate taxes from service charges based on name
      const tax = receiptData.taxes_or_charges
        .filter(tc => tc.name.toLowerCase().includes('tax') || tc.name.toLowerCase().includes('gst') || tc.name.toLowerCase().includes('vat'))
        .reduce((sum, tc) => sum + tc.amount, 0);
      
      const serviceCharge = receiptData.taxes_or_charges
        .filter(tc => tc.name.toLowerCase().includes('service') || tc.name.toLowerCase().includes('charge'))
        .reduce((sum, tc) => sum + tc.amount, 0);

      // Determine if this is tax-inclusive or tax-exclusive based on validation info
      const isGrandTotalEqualToItems = Math.abs(totalItemsSubtotal - finalTotal) <= 0.01;
      const taxScenario = isGrandTotalEqualToItems ? 'tax_inclusive' : 'tax_exclusive';
      
      // Calculate person splits based on their proportion of the FINAL TOTAL
      const personSplits: PersonSplit[] = participants.map((person, index) => {
        const assignedItems: Array<any> = [];
        
        // Collect assigned items for this person
        assignments.forEach(assignment => {
          if (assignment.assignedTo === person.id) {
            // Single assignment
            assignedItems.push({
              name: assignment.item.name,
              quantity: assignment.item.quantity,
              unit_price: assignment.item.unit_price,
              total_price: assignment.item.total_price,
            });
          } else if (assignment.isMultipleAssignment) {
            // Multiple assignment - show as split item
            const split = assignment.splits.find(s => s.personId === person.id);
            if (split) {
              assignedItems.push({
                name: assignment.item.name,
                quantity: assignment.item.quantity,
                unit_price: assignment.item.unit_price,
                total_price: split.amount, // Use the split amount instead of full item price
                isSplit: true,
                splitAmount: split.amount,
                splitPercentage: split.percentage,
              });
            }
          }
        });

        const itemsSubtotal = personSubtotals[index];
        const proportion = totalItemsSubtotal > 0 ? itemsSubtotal / totalItemsSubtotal : 0;
        
        // Each person pays their proportion of the FINAL TOTAL (grand_total)
        const personFinalTotal = roundToCents(finalTotal * proportion);
        
        // For display purposes, calculate what their tax/service charge "share" would be
        // But these are just for display - the actual payment is personFinalTotal
        let taxShare = 0;
        let serviceChargeShare = 0;
        
        if (taxScenario === 'tax_exclusive') {
          // In tax-exclusive scenario, we can show tax/service breakdown
          taxShare = roundToCents(tax * proportion);
          serviceChargeShare = roundToCents(serviceCharge * proportion);
        } else {
          // In tax-inclusive scenario, taxes are already included in the final total
          // Show them as 0 since they're already included in the item prices
          taxShare = 0;
          serviceChargeShare = 0;
        }

        return {
          person_id: person.id,
          person_name: person.name,
          items: assignedItems,
          subtotal: itemsSubtotal,
          tax_share: taxShare,
          service_charge_share: serviceChargeShare,
          discount_share: 0, // For now, assume no discount
          total: personFinalTotal, // This is what they actually pay
        };
      });

      // Validation: ensure all person totals add up to grand total
      const calculatedTotal = personSplits.reduce((sum, split) => sum + split.total, 0);
      const totalDifference = Math.abs(calculatedTotal - finalTotal);
      
      if (totalDifference > 0.01) {
        // Adjust the largest split to account for rounding differences
        const largestSplit = personSplits.reduce((max, split) => 
          split.total > max.total ? split : max, personSplits[0]);
        largestSplit.total = roundToCents(largestSplit.total + (finalTotal - calculatedTotal));
      }

      const totalTax = personSplits.reduce((sum, split) => sum + split.tax_share, 0);
      const totalServiceCharge = personSplits.reduce((sum, split) => sum + split.service_charge_share, 0);
      const totalDiscount = personSplits.reduce((sum, split) => sum + split.discount_share, 0);

      setState({
        personSplits,
        totalBill: roundToCents(finalTotal), // Always equals grand_total
        totalTax: roundToCents(totalTax),
        totalServiceCharge: roundToCents(totalServiceCharge),
        totalDiscount: roundToCents(totalDiscount),
        netTotal: roundToCents(finalTotal), // Always equals grand_total
        calculationMethod: method,
        error: null,
      });

      return personSplits;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Calculation failed';
      setState(prev => ({
        ...prev,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  const validateCalculation = useCallback((expectedTotal: number) => {
    const tolerance = 0.01;
    const difference = Math.abs(state.totalBill - expectedTotal);
    
    if (difference > tolerance) {
      setState(prev => ({
        ...prev,
        error: `Calculation validation failed: expected ${expectedTotal}, got ${state.totalBill}`,
      }));
      return false;
    }

    setState(prev => ({
      ...prev,
      error: null,
    }));
    return true;
  }, [state.totalBill]);

  const getPersonSummary = useCallback((personId: string) => {
    const personSplit = state.personSplits.find(split => split.person_id === personId);
    if (!personSplit) return null;

    return {
      person: {
        id: personSplit.person_id,
        name: personSplit.person_name,
      },
      items: personSplit.items,
      subtotal: personSplit.subtotal,
      tax: personSplit.tax_share,
      serviceCharge: personSplit.service_charge_share,
      discount: personSplit.discount_share,
      total: personSplit.total,
      itemCount: personSplit.items.length,
    };
  }, [state.personSplits]);

  const getCalculationSummary = useCallback(() => {
    return {
      method: state.calculationMethod,
      totals: {
        subtotal: state.personSplits.reduce((sum, split) => sum + split.subtotal, 0),
        tax: state.totalTax,
        serviceCharge: state.totalServiceCharge,
        discount: state.totalDiscount,
        total: state.totalBill,
      },
      personCount: state.personSplits.length,
      averagePerPerson: state.personSplits.length > 0 
        ? roundToCents(state.totalBill / state.personSplits.length)
        : 0,
    };
  }, [state]);

  const clearError = useCallback(() => {
    setState(prev => ({
      ...prev,
      error: null,
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      personSplits: [],
      totalBill: 0,
      totalTax: 0,
      totalServiceCharge: 0,
      totalDiscount: 0,
      netTotal: 0,
      calculationMethod: 'proportional',
      error: null,
    });
  }, []);

  // Memoized calculations
  const calculations = useMemo(() => ({
    totalItems: state.personSplits.reduce((sum, split) => sum + split.items.length, 0),
    averagePerPerson: state.personSplits.length > 0 
      ? roundToCents(state.totalBill / state.personSplits.length)
      : 0,
    isCalculationValid: state.error === null,
  }), [state.personSplits, state.totalBill, state.error]);

  return {
    state,
    calculations,
    actions: {
      calculateSplit,
      validateCalculation,
      getPersonSummary,
      getCalculationSummary,
      clearError,
      reset,
    },
  };
};