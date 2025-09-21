import React, { useState } from 'react';
import { X, Plus, Trash2, ZoomIn, ZoomOut } from 'lucide-react';
import { Button } from '@/components/UI/Button';
import { Card } from '@/components/UI/Card';

interface BillItem {
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

interface TaxOrCharge {
  name: string;
  amount: number;
  percent?: number;
}

interface StoreInfo {
  name: string;
  address?: string;
  phone?: string;
}

interface ExtractedData {
  items: BillItem[];
  taxes_or_charges: TaxOrCharge[];
  subtotal: number;
  grand_total: number;
  receipt_number: string;
  date: string;
  time: string;
  store: StoreInfo;
  payment_method: string;
  transaction_id?: string;
  notes?: string;
}

interface ValidationModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
  extractedData: ExtractedData;
  validationErrors: any;
  onValidate: (editedData: ExtractedData) => void;
}

export const ReceiptValidationModal: React.FC<ValidationModalProps> = ({
  isOpen,
  onClose,
  imageUrl,
  extractedData,
  validationErrors,
  onValidate,
}) => {
  const [items, setItems] = useState<BillItem[]>(extractedData.items || []);
  const [taxes, setTaxes] = useState<TaxOrCharge[]>(extractedData.taxes_or_charges || []);
  const [subtotal, setSubtotal] = useState(extractedData.subtotal || 0);
  const [grandTotal, setGrandTotal] = useState(extractedData.grand_total || 0);
  const [zoom, setZoom] = useState(1);

  if (!isOpen) return null;

  const handleAddItem = () => {
    setItems([...items, { name: '', quantity: 1, unit_price: 0, total_price: 0 }]);
  };

  const handleDeleteItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleItemChange = (index: number, field: keyof BillItem, value: any) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    setItems(updated);
  };

  const handleTaxChange = (index: number, field: keyof TaxOrCharge, value: any) => {
    const updated = [...taxes];
    updated[index] = { ...updated[index], [field]: value };
    setTaxes(updated);
  };

  const handleValidate = () => {
    const editedData: ExtractedData = {
      ...extractedData,
      items,
      taxes_or_charges: taxes,
      subtotal,
      grand_total: grandTotal,
    };
    onValidate(editedData);
  };

  // Extract error message
  const getErrorMessage = () => {
    if (!validationErrors) return null;
    
    if (typeof validationErrors === 'string') {
      return validationErrors;
    }
    
    if (validationErrors.message) {
      return validationErrors.message;
    }
    
    if (validationErrors.detail) {
      if (typeof validationErrors.detail === 'string') {
        return validationErrors.detail;
      }
      if (validationErrors.detail.message) {
        return validationErrors.detail.message;
      }
    }
    
    return JSON.stringify(validationErrors);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold">Review & Edit Receipt</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Error Display */}
        {validationErrors && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700 font-medium">Validation Error:</p>
            <p className="text-sm text-red-600 mt-1">{getErrorMessage()}</p>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Left Panel - Image Preview */}
          <div className="w-1/2 border-r p-4 flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Receipt Image</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}
                  className="p-1 hover:bg-gray-100 rounded"
                  type="button"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setZoom(Math.min(3, zoom + 0.25))}
                  className="p-1 hover:bg-gray-100 rounded"
                  type="button"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto bg-gray-50 rounded">
              <img
                src={imageUrl}
                alt="Receipt"
                style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
                className="max-w-none"
              />
            </div>
          </div>

          {/* Right Panel - Editable Fields */}
          <div className="w-1/2 p-4 overflow-auto">
            {/* Items Section */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">Items</h3>
                <Button size="sm" variant="outline" onClick={handleAddItem} type="button">
                  <Plus className="h-4 w-4 mr-1" /> Add Item
                </Button>
              </div>
              <div className="space-y-2">
                {items.map((item, index) => (
                  <Card key={index} className="p-3">
                    <div className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={item.name}
                        onChange={(e) => handleItemChange(index, 'name', e.target.value)}
                        placeholder="Item name"
                        className="flex-1 px-2 py-1 border rounded text-sm"
                      />
                      <button
                        onClick={() => handleDeleteItem(index)}
                        className="p-1 text-red-500 hover:bg-red-50 rounded"
                        type="button"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => handleItemChange(index, 'quantity', parseInt(e.target.value) || 0)}
                        placeholder="Qty"
                        className="px-2 py-1 border rounded text-sm"
                      />
                      <input
                        type="number"
                        step="0.01"
                        value={item.unit_price}
                        onChange={(e) => handleItemChange(index, 'unit_price', parseFloat(e.target.value) || 0)}
                        placeholder="Unit Price"
                        className="px-2 py-1 border rounded text-sm"
                      />
                      <input
                        type="number"
                        step="0.01"
                        value={item.total_price}
                        onChange={(e) => handleItemChange(index, 'total_price', parseFloat(e.target.value) || 0)}
                        placeholder="Total"
                        className="px-2 py-1 border rounded text-sm"
                      />
                    </div>
                  </Card>
                ))}
              </div>
            </div>

            {/* Taxes Section */}
            <div className="mb-6 pb-6 border-b">
              <h3 className="font-semibold text-gray-900 mb-3">Taxes & Charges</h3>
              <div className="space-y-2">
                {taxes.map((tax, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={tax.name}
                      onChange={(e) => handleTaxChange(index, 'name', e.target.value)}
                      placeholder="Tax/Charge name"
                      className="flex-1 px-2 py-1 border rounded text-sm"
                    />
                    <input
                      type="number"
                      step="0.01"
                      value={tax.amount}
                      onChange={(e) => handleTaxChange(index, 'amount', parseFloat(e.target.value) || 0)}
                      placeholder="Amount"
                      className="w-24 px-2 py-1 border rounded text-sm"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Totals Section */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900">Totals</h3>
              <div className="flex justify-between items-center">
                <label className="text-sm text-gray-600">Subtotal</label>
                <input
                  type="number"
                  step="0.01"
                  value={subtotal}
                  onChange={(e) => setSubtotal(parseFloat(e.target.value) || 0)}
                  className="w-32 px-2 py-1 border rounded text-sm"
                />
              </div>
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-gray-900">Grand Total</label>
                <input
                  type="number"
                  step="0.01"
                  value={grandTotal}
                  onChange={(e) => setGrandTotal(parseFloat(e.target.value) || 0)}
                  className="w-32 px-2 py-1 border rounded text-sm font-medium"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <Button variant="outline" onClick={onClose} type="button">Cancel</Button>
          <Button onClick={handleValidate} type="button">Validate</Button>
        </div>
      </div>
    </div>
  );
};