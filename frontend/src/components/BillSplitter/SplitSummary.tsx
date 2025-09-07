import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { PersonSplit } from '@/types/split.types';
import { formatCurrency } from '@/utils/formatters';
import { Receipt, User, Calculator, Download, Share2, Users } from 'lucide-react';

export interface SplitSummaryProps {
  personSplits: PersonSplit[];
  totalBill: number;
  totalTax: number;
  totalServiceCharge: number;
  totalDiscount: number;
  onStartOver: () => void;
  onShare: () => void;
  onDownload: () => void;
  disabled?: boolean;
}

export const SplitSummary: React.FC<SplitSummaryProps> = ({
  personSplits,
  totalBill,
  totalTax,
  totalServiceCharge,
  totalDiscount,
  onStartOver,
  onShare,
  onDownload,
  disabled = false,
}) => {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <Calculator className="h-8 w-8 text-green-600" />
          </div>
          <CardTitle>Bill Split Complete!</CardTitle>
          <CardDescription>
            Here's how much each person owes
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(totalBill)}
            </div>
            <div className="text-sm text-gray-500">Total Bill</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(totalTax)}
            </div>
            <div className="text-sm text-gray-500">Tax</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(totalServiceCharge)}
            </div>
            <div className="text-sm text-gray-500">Service Charge</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(totalDiscount)}
            </div>
            <div className="text-sm text-gray-500">Discount</div>
          </CardContent>
        </Card>
      </div>

      {/* Person Splits */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Individual Splits</h3>
        {personSplits.map((split, index) => (
          <Card key={split.person_id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="h-5 w-5 text-primary-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">{split.person_name}</h4>
                    <p className="text-sm text-gray-500">
                      {split.items.length} item(s)
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatCurrency(split.total)}
                  </div>
                  <div className="text-sm text-gray-500">Total</div>
                </div>
              </div>

              {/* Items breakdown */}
              <div className="space-y-2">
                <h5 className="text-sm font-medium text-gray-700">Items:</h5>
                <div className="space-y-1">
                  {split.items.map((item: any, itemIndex) => (
                    <div key={itemIndex} className="flex justify-between text-sm">
                      <span className="text-gray-600 flex items-center">
                        {item.quantity}x {item.name}
                        {item.isSplit && (
                          <span className="ml-2 inline-flex items-center">
                            <Users className="h-3 w-3 text-blue-500 mr-1" />
                            <span className="text-xs text-blue-600">
                              ({item.splitPercentage?.toFixed(1)}%)
                            </span>
                          </span>
                        )}
                      </span>
                      <span className="font-medium">
                        {formatCurrency(item.total_price)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cost breakdown */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Subtotal:</span>
                    <span>{formatCurrency(split.subtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tax:</span>
                    <span>{formatCurrency(split.tax_share)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Service Charge:</span>
                    <span>{formatCurrency(split.service_charge_share)}</span>
                  </div>
                  {split.discount_share > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Discount:</span>
                      <span className="text-green-600">-{formatCurrency(split.discount_share)}</span>
                    </div>
                  )}
                  <div className="flex justify-between font-semibold text-gray-900 pt-2 border-t border-gray-200">
                    <span>Total:</span>
                    <span>{formatCurrency(split.total)}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Action Buttons */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-wrap gap-3 justify-center">
            <Button
              onClick={onStartOver}
              variant="outline"
              disabled={disabled}
            >
              Split Another Bill
            </Button>
            <Button
              onClick={handlePrint}
              variant="outline"
              disabled={disabled}
              leftIcon={<Receipt className="h-4 w-4" />}
            >
              Print Summary
            </Button>
            <Button
              onClick={onDownload}
              variant="outline"
              disabled={disabled}
              leftIcon={<Download className="h-4 w-4" />}
            >
              Download PDF
            </Button>
            <Button
              onClick={onShare}
              disabled={disabled}
              leftIcon={<Share2 className="h-4 w-4" />}
            >
              Share Results
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};