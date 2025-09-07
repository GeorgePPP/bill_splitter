import React from 'react';
import { Card, CardContent } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { BillItem } from '@/types/bill.types';
import { ItemAssignment } from '@/hooks/useItemAssignment';
import { formatCurrency } from '@/utils/formatters';
import { ShoppingCart, Package, Users, X } from 'lucide-react';

export interface BillItemCardProps {
  item: BillItem;
  index: number;
  assignment: ItemAssignment;
  participants: Array<{ id: string; name: string }>;
  onAssign: (itemIndex: number, personId: string) => { requiresConfirmation: boolean; duplicateInfo: any; requiresSplitChoice?: boolean } | void;
  onUnassign: (itemIndex: number) => void;
  onRemovePersonFromSplit: (itemIndex: number, personId: string) => void;
  disabled?: boolean;
}

export const BillItemCard: React.FC<BillItemCardProps> = ({
  item,
  index,
  assignment,
  participants,
  onAssign,
  onUnassign,
  onRemovePersonFromSplit,
  disabled = false,
}) => {
  const handleAssign = (personId: string) => {
    onAssign(index, personId);
  };

  const handleUnassign = () => {
    onUnassign(index);
  };

  const handleRemoveFromSplit = (personId: string) => {
    onRemovePersonFromSplit(index, personId);
  };

  const getPersonName = (personId: string) => {
    return participants.find(p => p.id === personId)?.name || 'Unknown';
  };

  const isAssigned = assignment.assignedTo || assignment.isMultipleAssignment;
  const assignedPersonIds = assignment.isMultipleAssignment 
    ? assignment.splits.map(s => s.personId)
    : assignment.assignedTo 
      ? [assignment.assignedTo]
      : [];

  const unassignedParticipants = participants.filter(p => !assignedPersonIds.includes(p.id));

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
              {assignment.isMultipleAssignment && (
                <Users className="h-4 w-4 text-blue-500" title="Split among multiple people" />
              )}
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Qty: {item.quantity}</span>
              <span>@ {formatCurrency(item.unit_price)}</span>
              <span className="font-medium text-gray-900">
                Total: {formatCurrency(item.total_price)}
              </span>
            </div>
          </div>

          <div className="flex-shrink-0 ml-4">
            {isAssigned ? (
              <div className="space-y-2">
                {/* Single assignment */}
                {assignment.assignedTo && (
                  <div className="flex items-center space-x-2">
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {getPersonName(assignment.assignedTo)}
                      </p>
                      <p className="text-xs text-gray-500">Fully assigned</p>
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
                )}

                {/* Multiple assignment splits */}
                {assignment.isMultipleAssignment && (
                  <div className="space-y-1">
                    <div className="text-xs text-gray-500 mb-1">Split assignment:</div>
                    {assignment.splits.map((split) => (
                      <div key={split.personId} className="flex items-center space-x-2 text-sm">
                        <div className="flex-1 text-right">
                          <div className="font-medium text-gray-900">
                            {getPersonName(split.personId)}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatCurrency(split.amount)} ({split.percentage.toFixed(1)}%)
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveFromSplit(split.personId)}
                          disabled={disabled}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 p-1"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add more people button for existing assignments */}
                {unassignedParticipants.length > 0 && (
                  <div className="border-t border-gray-200 pt-2 mt-2">
                    <div className="text-xs text-gray-500 mb-1">Add more people:</div>
                    <div className="flex flex-wrap gap-1">
                      {unassignedParticipants.map((person) => (
                        <Button
                          key={person.id}
                          variant="outline"
                          size="sm"
                          onClick={() => handleAssign(person.id)}
                          disabled={disabled}
                          className="text-xs px-2 py-1"
                        >
                          + {person.name}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
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