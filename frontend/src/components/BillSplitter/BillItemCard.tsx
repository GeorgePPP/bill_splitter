import React from 'react';
import { Card, CardContent } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { BillItem } from '@/types/bill.types';
import { formatCurrency } from '@/utils/formatters';
import { ShoppingCart, Package } from 'lucide-react';

export interface BillItemCardProps {
  item: BillItem;
  index: number;
  assignedTo?: string;
  participants: Array<{ id: string; name: string }>;
  onAssign: (itemIndex: number, personId: string) => { requiresConfirmation: boolean; duplicateInfo: any } | void;
  onUnassign: (itemIndex: number) => void;
  disabled?: boolean;
}

export const BillItemCard: React.FC<BillItemCardProps> = ({
  item,
  index,
  assignedTo,
  participants,
  onAssign,
  onUnassign,
  disabled = false,
}) => {
  const handleAssign = (personId: string) => {
    onAssign(index, personId);
  };

  const handleUnassign = () => {
    onUnassign(index);
  };

  const assignedPerson = participants.find(p => p.id === assignedTo);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <Package className="h-4 w-4 text-gray-400" />
              <h4 className="font-medium text-gray-900 truncate">
                {item.name}
              </h4>
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Qty: {item.quantity}</span>
              <span>@ {formatCurrency(item.unit_price)}</span>
              <span className="font-medium text-gray-900">
                Total: {formatCurrency(item.total)}
              </span>
            </div>
          </div>

          <div className="flex-shrink-0 ml-4">
            {assignedTo ? (
              <div className="flex items-center space-x-2">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {assignedPerson?.name}
                  </p>
                  <p className="text-xs text-gray-500">Assigned</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleUnassign}
                  disabled={disabled}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  Remove
                </Button>
              </div>
            ) : (
              <div className="text-right">
                <p className="text-sm text-gray-500 mb-2">Assign to:</p>
                <div className="flex flex-wrap gap-1">
                  {participants.map((person) => (
                    <Button
                      key={person.id}
                      variant="outline"
                      size="sm"
                      onClick={() => handleAssign(person.id)}
                      disabled={disabled}
                      className="text-xs"
                    >
                      {person.name}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
