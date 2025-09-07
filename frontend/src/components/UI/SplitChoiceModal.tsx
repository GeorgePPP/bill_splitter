import React, { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { Input } from './Input';
import { BillItem } from '@/types/bill.types';
import { Person } from '@/types/person.types';
import { ItemSplit } from '@/hooks/useItemAssignment';
import { formatCurrency } from '@/utils/formatters';
import { Users, DollarSign, Percent, AlertCircle } from 'lucide-react';

export interface SplitChoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (splitType: 'equal' | 'unequal', customSplits?: ItemSplit[]) => void;
  item: BillItem;
  personIds: string[];
  participants: Person[];
}

export const SplitChoiceModal: React.FC<SplitChoiceModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  item,
  personIds,
  participants,
}) => {
  const [splitType, setSplitType] = useState<'equal' | 'unequal'>('equal');
  const [customSplits, setCustomSplits] = useState<ItemSplit[]>(() => {
    const equalAmount = item.total_price / personIds.length;
    return personIds.map(personId => ({
      personId,
      amount: Math.round(equalAmount * 100) / 100,
      percentage: Math.round((100 / personIds.length) * 100) / 100,
    }));
  });
  const [error, setError] = useState<string>('');

  const getPersonName = (personId: string) => {
    return participants.find(p => p.id === personId)?.name || 'Unknown';
  };

  const handleCustomSplitChange = (personId: string, amount: number) => {
    setCustomSplits(prev => {
      const updated = prev.map(split => 
        split.personId === personId 
          ? {
              ...split,
              amount: Math.round(amount * 100) / 100,
              percentage: Math.round((amount / item.total_price) * 100 * 100) / 100,
            }
          : split
      );
      return updated;
    });
    setError('');
  };

  const getTotalAssigned = () => {
    return customSplits.reduce((sum, split) => sum + split.amount, 0);
  };

  const getRemaining = () => {
    return Math.round((item.total_price - getTotalAssigned()) * 100) / 100;
  };

  const validateSplits = () => {
    const total = getTotalAssigned();
    const difference = Math.abs(total - item.total_price);
    
    if (difference > 0.01) {
      setError(`Total splits (${formatCurrency(total)}) must equal item total (${formatCurrency(item.total_price)})`);
      return false;
    }

    // Check for negative or zero amounts
    const hasInvalidAmount = customSplits.some(split => split.amount <= 0);
    if (hasInvalidAmount) {
      setError('All split amounts must be greater than zero');
      return false;
    }

    setError('');
    return true;
  };

  const handleConfirm = () => {
    if (splitType === 'equal') {
      onConfirm('equal');
    } else {
      if (validateSplits()) {
        onConfirm('unequal', customSplits);
      }
    }
  };

  const handleSplitTypeChange = (type: 'equal' | 'unequal') => {
    setSplitType(type);
    setError('');
    
    if (type === 'equal') {
      const equalAmount = item.total_price / personIds.length;
      setCustomSplits(personIds.map(personId => ({
        personId,
        amount: Math.round(equalAmount * 100) / 100,
        percentage: Math.round((100 / personIds.length) * 100) / 100,
      })));
    }
  };

  const redistributeRemaining = () => {
    const remaining = getRemaining();
    if (Math.abs(remaining) > 0.01) {
      setCustomSplits(prev => {
        const updated = [...prev];
        updated[0].amount += remaining;
        updated[0].amount = Math.round(updated[0].amount * 100) / 100;
        updated[0].percentage = Math.round((updated[0].amount / item.total_price) * 100 * 100) / 100;
        return updated;
      });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Split Item Assignment" size="lg">
      <div className="space-y-6">
        {/* Item Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">{item.name}</h4>
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Quantity: {item.quantity}</span>
            <span className="font-medium text-gray-900">
              Total: {formatCurrency(item.total_price)}
            </span>
          </div>
        </div>

        {/* People involved */}
        <div>
          <h5 className="text-sm font-medium text-gray-700 mb-2">People sharing this item:</h5>
          <div className="flex flex-wrap gap-2">
            {personIds.map(personId => (
              <div key={personId} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                {getPersonName(personId)}
              </div>
            ))}
          </div>
        </div>

        {/* Split type selection */}
        <div>
          <h5 className="text-sm font-medium text-gray-700 mb-3">How would you like to split this item?</h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <button
              onClick={() => handleSplitTypeChange('equal')}
              className={`p-4 border-2 rounded-lg text-left transition-colors ${
                splitType === 'equal'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Users className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="font-medium text-gray-900">Split Equally</div>
                  <div className="text-sm text-gray-500">
                    {formatCurrency(item.total_price / personIds.length)} per person
                  </div>
                </div>
              </div>
            </button>

            <button
              onClick={() => handleSplitTypeChange('unequal')}
              className={`p-4 border-2 rounded-lg text-left transition-colors ${
                splitType === 'unequal'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-3">
                <DollarSign className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="font-medium text-gray-900">Custom Split</div>
                  <div className="text-sm text-gray-500">
                    Specify individual amounts
                  </div>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Custom split inputs */}
        {splitType === 'unequal' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h5 className="text-sm font-medium text-gray-700">Specify amounts:</h5>
              {Math.abs(getRemaining()) > 0.01 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={redistributeRemaining}
                  className="text-xs"
                >
                  Auto-adjust remaining
                </Button>
              )}
            </div>
            
            <div className="space-y-3">
              {customSplits.map((split, index) => (
                <div key={split.personId} className="flex items-center space-x-3">
                  <div className="w-24 text-sm font-medium text-gray-700">
                    {getPersonName(split.personId)}
                  </div>
                  <div className="flex-1">
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      max={item.total_price}
                      value={split.amount}
                      onChange={(e) => handleCustomSplitChange(split.personId, parseFloat(e.target.value) || 0)}
                      leftIcon={<DollarSign className="h-4 w-4" />}
                      className="text-sm"
                    />
                  </div>
                  <div className="w-16 text-sm text-gray-500">
                    {split.percentage.toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">Total assigned:</span>
                <span className="font-medium">{formatCurrency(getTotalAssigned())}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">Item total:</span>
                <span className="font-medium">{formatCurrency(item.total_price)}</span>
              </div>
              <div className="border-t border-gray-200 mt-2 pt-2">
                <div className="flex justify-between items-center text-sm">
                  <span className={getRemaining() === 0 ? 'text-green-600' : 'text-red-600'}>
                    Remaining:
                  </span>
                  <span className={`font-medium ${getRemaining() === 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(getRemaining())}
                  </span>
                </div>
              </div>
            </div>

            {Math.abs(getRemaining()) > 0.01 && (
              <div className="flex items-center space-x-2 text-amber-600 text-sm">
                <AlertCircle className="h-4 w-4" />
                <span>
                  {getRemaining() > 0 
                    ? `${formatCurrency(getRemaining())} remaining to be assigned`
                    : `Over-assigned by ${formatCurrency(Math.abs(getRemaining()))}`
                  }
                </span>
              </div>
            )}
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleConfirm}>
            Confirm Split
          </Button>
        </div>
      </div>
    </Modal>
  );
};