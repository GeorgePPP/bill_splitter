import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/UI/Card';
import { formatCurrency, formatPercentage } from '@/utils/formatters';
import { Calculator, Percent, DollarSign } from 'lucide-react';

export interface TaxCalculatorProps {
  subtotal: number;
  tax: number;
  serviceCharge: number;
  discount: number;
  total: number;
  taxRate?: number;
  serviceChargeRate?: number;
  discountRate?: number;
}

export const TaxCalculator: React.FC<TaxCalculatorProps> = ({
  subtotal,
  tax,
  serviceCharge,
  discount,
  total,
  taxRate,
  serviceChargeRate,
  discountRate,
}) => {
  const calculatedTaxRate = taxRate || (subtotal > 0 ? (tax / subtotal) : 0);
  const calculatedServiceChargeRate = serviceChargeRate || (subtotal > 0 ? (serviceCharge / subtotal) : 0);
  const calculatedDiscountRate = discountRate || (subtotal > 0 ? (discount / subtotal) : 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Calculator className="h-5 w-5" />
          <span>Tax & Fee Breakdown</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">Subtotal</span>
            </div>
            <span className="font-semibold">{formatCurrency(subtotal)}</span>
          </div>

          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="flex items-center space-x-2">
              <Percent className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">Tax</span>
              {calculatedTaxRate > 0 && (
                <span className="text-xs text-gray-500">
                  ({formatPercentage(calculatedTaxRate)})
                </span>
              )}
            </div>
            <span className="font-semibold text-red-600">
              +{formatCurrency(tax)}
            </span>
          </div>

          {serviceCharge > 0 && (
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <div className="flex items-center space-x-2">
                <Calculator className="h-4 w-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">Service Charge</span>
                {calculatedServiceChargeRate > 0 && (
                  <span className="text-xs text-gray-500">
                    ({formatPercentage(calculatedServiceChargeRate)})
                  </span>
                )}
              </div>
              <span className="font-semibold text-red-600">
                +{formatCurrency(serviceCharge)}
              </span>
            </div>
          )}

          {discount > 0 && (
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <div className="flex items-center space-x-2">
                <Percent className="h-4 w-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">Discount</span>
                {calculatedDiscountRate > 0 && (
                  <span className="text-xs text-gray-500">
                    ({formatPercentage(calculatedDiscountRate)})
                  </span>
                )}
              </div>
              <span className="font-semibold text-green-600">
                -{formatCurrency(discount)}
              </span>
            </div>
          )}

          <div className="flex justify-between items-center py-3 border-t-2 border-gray-200 bg-gray-50 rounded-lg px-3">
            <span className="text-lg font-bold text-gray-900">Total</span>
            <span className="text-lg font-bold text-gray-900">
              {formatCurrency(total)}
            </span>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(subtotal)}
            </div>
            <div className="text-xs text-gray-500">Base Amount</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(tax + serviceCharge - discount)}
            </div>
            <div className="text-xs text-gray-500">Fees & Taxes</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
