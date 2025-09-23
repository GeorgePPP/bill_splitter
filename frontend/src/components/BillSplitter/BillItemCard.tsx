import React from 'react';
import { Card, CardContent } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { BillItem } from '@/types/bill.types';
import { ItemAssignment } from '@/hooks/useItemAssignment';
import { formatCurrency } from '@/utils/formatters';
import { Package, Users, Check } from 'lucide-react';

export interface BillItemCardProps {
  item: BillItem;
  index: number;
  assignment: ItemAssignment;
  participants: Array<{ id: string; name: string }>;
  onAssign: (itemIndex: number, personId: string) => { requiresConfirmation: boolean; duplicateInfo: any; requiresSplitChoice?: boolean } | void;
  onUnassign: (itemIndex: number) => void;
  onRemovePersonFromSplit: (itemIndex: number, personId: string) => void;
  onMultipleAssign: (itemIndex: number, personIds: string[], forceCustomSplit?: boolean) => void;
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
  onMultipleAssign,
  disabled = false,
}) => {
  const handleAssign = (personId: string) => {
    // Get current selection state
    const currentAssignedPeople = assignment.isMultipleAssignment 
      ? assignment.splits.map(s => s.personId)
      : assignment.assignedTo 
        ? [assignment.assignedTo]
        : [];
    
    // Toggle person selection and auto-assign immediately
    const newSelectedPeople = currentAssignedPeople.includes(personId) 
      ? currentAssignedPeople.filter(id => id !== personId)
      : [...currentAssignedPeople, personId];
    
    // Auto-assign immediately with equal split by default
    if (newSelectedPeople.length > 0) {
      onMultipleAssign(index, newSelectedPeople, false); // false = don't force custom split
    } else {
      // If no one selected, unassign the item
      onUnassign(index);
    }
  };


  const handleCustomSplit = () => {
    // Trigger the custom split modal
    const personIds = assignment.isMultipleAssignment 
      ? assignment.splits.map(s => s.personId)
      : [];
    
    if (personIds.length > 1) {
      // This will open the split choice modal for custom splits
      onMultipleAssign(index, personIds, true); // Pass true to indicate custom split request
    }
  };

  const getPersonName = (personId: string) => {
    return participants.find(p => p.id === personId)?.name || 'Unknown';
  };


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
              {/* Custom split link - positioned in top right */}
              {assignment.isMultipleAssignment && assignment.splits.length > 1 && (
                <button
                  onClick={handleCustomSplit}
                  disabled={disabled}
                  className="ml-auto text-xs text-blue-600 hover:text-blue-700 underline cursor-pointer"
                >
                  Custom split
                </button>
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
            <div className="text-right">
              <p className="text-sm text-gray-500 mb-2">Select people:</p>
              <div className="flex flex-wrap gap-1">
                {participants.map((person) => {
                  const isSelected = assignment.isMultipleAssignment 
                    ? assignment.splits.some(s => s.personId === person.id)
                    : assignment.assignedTo === person.id;
                  
                  return (
                    <Button
                      key={person.id}
                      variant={isSelected ? "primary" : "outline"}
                      size="sm"
                      onClick={() => handleAssign(person.id)}
                      disabled={disabled}
                      className="text-xs px-2 py-1"
                    >
                      {isSelected && <Check className="h-3 w-3 mr-1" />}
                      {person.name}
                    </Button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};