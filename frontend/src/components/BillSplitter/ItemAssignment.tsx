import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/UI/Card';
import { Button } from '@/components/UI/Button';
import { BillItemCard } from './BillItemCard';
import { BillItem } from '@/types/bill.types';
import { Person } from '@/types/person.types';
import { ShoppingCart, CheckCircle, AlertCircle } from 'lucide-react';

export interface ItemAssignmentProps {
  items: BillItem[];
  participants: Person[];
  assignments: Array<{
    item: BillItem;
    assignedTo: string | null;
  }>;
  onAssignItem: (itemIndex: number, personId: string) => void;
  onUnassignItem: (itemIndex: number) => void;
  onNext: () => void;
  onBack: () => void;
  disabled?: boolean;
}

export const ItemAssignment: React.FC<ItemAssignmentProps> = ({
  items,
  participants,
  assignments,
  onAssignItem,
  onUnassignItem,
  onNext,
  onBack,
  disabled = false,
}) => {
  const assignedCount = assignments.filter(a => a.assignedTo !== null).length;
  const totalCount = assignments.length;
  const allAssigned = assignedCount === totalCount;

  return (
    <Card className="max-w-4xl mx-auto">
      <CardHeader className="text-center">
        <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
          <ShoppingCart className="h-8 w-8 text-primary-600" />
        </div>
        <CardTitle>Assign Items to People</CardTitle>
        <CardDescription>
          Click on a person's name to assign each item to them
        </CardDescription>
        
        <div className="flex items-center justify-center space-x-4 mt-4">
          <div className="flex items-center space-x-2">
            {allAssigned ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-500" />
            )}
            <span className="text-sm font-medium">
              {assignedCount} of {totalCount} items assigned
            </span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <div className="grid gap-4">
          {assignments.map((assignment, index) => (
            <BillItemCard
              key={`${assignment.item.name}-${index}`}
              item={assignment.item}
              index={index}
              assignedTo={assignment.assignedTo}
              participants={participants}
              onAssign={onAssignItem}
              onUnassign={onUnassignItem}
              disabled={disabled}
            />
          ))}
        </div>

        {!allAssigned && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              <p className="text-sm text-yellow-700">
                Please assign all items before proceeding. {totalCount - assignedCount} item(s) remaining.
              </p>
            </div>
          </div>
        )}

        <div className="flex justify-between pt-4">
          <Button
            variant="outline"
            onClick={onBack}
            disabled={disabled}
          >
            Back
          </Button>
          <Button
            onClick={onNext}
            disabled={!allAssigned || disabled}
          >
            Calculate Split
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
