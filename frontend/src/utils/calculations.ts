export const calculateSubtotal = (items: Array<{ quantity: number; unit_price: number }>): number => {
  return items.reduce((total, item) => total + (item.quantity * item.unit_price), 0);
};

export const calculateTax = (subtotal: number, taxRate: number): number => {
  return subtotal * taxRate;
};

export const calculateServiceCharge = (subtotal: number, serviceChargeRate: number): number => {
  return subtotal * serviceChargeRate;
};

export const calculateDiscount = (subtotal: number, discountRate: number): number => {
  return subtotal * discountRate;
};

export const calculateTotal = (
  subtotal: number,
  tax: number,
  serviceCharge: number,
  discount: number
): number => {
  return subtotal + tax + serviceCharge - discount;
};

export const calculateProportionalShare = (
  personAmount: number,
  totalAmount: number,
  totalToDistribute: number
): number => {
  if (totalAmount === 0) return 0;
  return (personAmount / totalAmount) * totalToDistribute;
};

export const calculateEqualShare = (totalAmount: number, numberOfPeople: number): number => {
  return totalAmount / numberOfPeople;
};

export const roundToCents = (amount: number): number => {
  return Math.round(amount * 100) / 100;
};

export const validateCalculation = (
  calculatedTotal: number,
  expectedTotal: number,
  tolerance: number = 0.01
): boolean => {
  return Math.abs(calculatedTotal - expectedTotal) <= tolerance;
};

export const distributeAmount = (
  amounts: number[],
  totalToDistribute: number,
  method: 'proportional' | 'equal' = 'proportional'
): number[] => {
  if (method === 'equal') {
    const share = totalToDistribute / amounts.length;
    return amounts.map(() => share);
  }
  
  const totalAmount = amounts.reduce((sum, amount) => sum + amount, 0);
  if (totalAmount === 0) {
    return amounts.map(() => 0);
  }
  
  return amounts.map(amount => 
    roundToCents((amount / totalAmount) * totalToDistribute)
  );
};
