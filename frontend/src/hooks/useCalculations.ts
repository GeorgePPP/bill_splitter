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
      // Calculate each person's subtotal from assigned items
      const personSubtotals = participants.map(person => {
        const assignedItems = assignments
          .filter(assignment => assignment.assignedTo === person.id)
          .map(assignment => assignment.item);
        
        return calculateSubtotal(assignedItems);
      });

      // Calculate total taxes and charges for validation (if needed later)
      
      // For backward compatibility, separate taxes from service charges based on name
      const tax = receiptData.taxes_or_charges
        .filter(tc => tc.name.toLowerCase().includes('tax') || tc.name.toLowerCase().includes('gst') || tc.name.toLowerCase().includes('vat'))
        .reduce((sum, tc) => sum + tc.amount, 0);
      
      const serviceCharge = receiptData.taxes_or_charges
        .filter(tc => tc.name.toLowerCase().includes('service') || tc.name.toLowerCase().includes('charge'))
        .reduce((sum, tc) => sum + tc.amount, 0);

      // Calculate tax distribution
      const taxDistribution = method === 'proportional' 
        ? distributeAmount(personSubtotals, tax, 'proportional')
        : distributeAmount(personSubtotals, tax, 'equal');

      // Calculate service charge distribution
      const serviceChargeDistribution = method === 'proportional'
        ? distributeAmount(personSubtotals, serviceCharge, 'proportional')
        : distributeAmount(personSubtotals, serviceCharge, 'equal');

      // For now, assume no discount (can be added later if needed)
      const discountDistribution = participants.map(() => 0);

      // Create person splits
      const personSplits: PersonSplit[] = participants.map((person, index) => {
        const assignedItems = assignments
          .filter(assignment => assignment.assignedTo === person.id)
          .map(assignment => assignment.item);

        const subtotal = personSubtotals[index];
        const taxShare = roundToCents(taxDistribution[index]);
        const serviceChargeShare = roundToCents(serviceChargeDistribution[index]);
        const discountShare = roundToCents(discountDistribution[index]);
        const total = roundToCents(subtotal + taxShare + serviceChargeShare - discountShare);

        return {
          person_id: person.id,
          person_name: person.name,
          items: assignedItems,
          subtotal,
          tax_share: taxShare,
          service_charge_share: serviceChargeShare,
          discount_share: discountShare,
          total,
        };
      });

      const totalBill = personSplits.reduce((sum, split) => sum + split.total, 0);
      const totalTax = personSplits.reduce((sum, split) => sum + split.tax_share, 0);
      const totalServiceCharge = personSplits.reduce((sum, split) => sum + split.service_charge_share, 0);
      const totalDiscount = personSplits.reduce((sum, split) => sum + split.discount_share, 0);

      setState({
        personSplits,
        totalBill: roundToCents(totalBill),
        totalTax: roundToCents(totalTax),
        totalServiceCharge: roundToCents(totalServiceCharge),
        totalDiscount: roundToCents(totalDiscount),
        netTotal: roundToCents(totalBill),
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
