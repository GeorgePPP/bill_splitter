import React, { useEffect, useMemo, useRef, useState } from 'react';
import { X, Plus, Trash2, ZoomIn, ZoomOut, CheckCircle, AlertCircle } from 'lucide-react';
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
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const imageContainerRef = useRef<HTMLDivElement | null>(null);
  const didInitViewRef = useRef(false);
  const panRef = useRef<{
    isPanning: boolean;
    startX: number;
    startY: number;
    panX: number;
    panY: number;
  }>({
    isPanning: false,
    startX: 0,
    startY: 0,
    panX: 0,
    panY: 0,
  });

  const roundMoney = (value: number) => Math.round((value + Number.EPSILON) * 100) / 100;
  const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

  const clampPan = (candidatePan: { x: number; y: number }, nextZoom: number) => {
    const scaledWidth = imageSize.width * nextZoom;
    const scaledHeight = imageSize.height * nextZoom;

    const maxX = Math.max(0, (scaledWidth - containerSize.width) / 2);
    const maxY = Math.max(0, (scaledHeight - containerSize.height) / 2);

    return {
      x: clamp(candidatePan.x, -maxX, maxX),
      y: clamp(candidatePan.y, -maxY, maxY),
    };
  };

  const normalizeItem = (item: BillItem): BillItem => {
    const quantity = Number.isFinite(item.quantity) ? item.quantity : 0;
    const unit_price = Number.isFinite(item.unit_price) ? item.unit_price : 0;
    return {
      ...item,
      quantity,
      unit_price,
      total_price: roundMoney(quantity * unit_price),
    };
  };

  const [items, setItems] = useState<BillItem[]>(() =>
    (extractedData.items || []).map(normalizeItem)
  );
  const [taxes, setTaxes] = useState<TaxOrCharge[]>(() => extractedData.taxes_or_charges || []);

  if (!isOpen) return null;

  useEffect(() => {
    if (!isOpen) return;
    setItems((extractedData.items || []).map(normalizeItem));
    setTaxes(extractedData.taxes_or_charges || []);
    setZoom(1);
    setPan({ x: 0, y: 0 });
    didInitViewRef.current = false;
  }, [isOpen, extractedData]);

  useEffect(() => {
    const container = imageContainerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      setContainerSize({ width, height });
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    if (didInitViewRef.current) return;
    if (containerSize.width <= 0 || containerSize.height <= 0) return;
    if (imageSize.width <= 0 || imageSize.height <= 0) return;

    const fitZoom = Math.min(
      1,
      containerSize.width / imageSize.width,
      containerSize.height / imageSize.height
    );

    didInitViewRef.current = true;
    setZoom(fitZoom);
    setPan({ x: 0, y: 0 });
  }, [isOpen, containerSize, imageSize]);

  const handleAddItem = () => {
    setItems([...items, { name: '', quantity: 1, unit_price: 0, total_price: 0 }]);
  };

  const handleDeleteItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleItemChange = (index: number, field: keyof BillItem, value: any) => {
    if (field === 'total_price') return; // computed

    setItems(prev => {
      const updated = [...prev];
      const current = updated[index];
      if (!current) return prev;

      const next: BillItem = { ...current, [field]: value };
      if (field === 'quantity' || field === 'unit_price') {
        const quantity = Number.isFinite(next.quantity) ? next.quantity : 0;
        const unit_price = Number.isFinite(next.unit_price) ? next.unit_price : 0;
        next.total_price = roundMoney(quantity * unit_price);
      }

      updated[index] = next;
      return updated;
    });
  };

  const handleTaxChange = (index: number, field: keyof TaxOrCharge, value: any) => {
    const updated = [...taxes];
    updated[index] = { ...updated[index], [field]: value };
    setTaxes(updated);
  };

  const handleAddTax = () => {
    setTaxes(prev => [...prev, { name: '', amount: 0 }]);
  };

  const handleDeleteTax = (index: number) => {
    setTaxes(prev => prev.filter((_, i) => i !== index));
  };

  const subtotal = useMemo(() => roundMoney(items.reduce((sum, item) => sum + (item.total_price || 0), 0)), [items]);
  const taxesAndChargesTotal = useMemo(() => {
    const total = taxes.reduce((sum, tax) => {
      const amount = Number.isFinite(tax.amount) && tax.amount !== 0
        ? tax.amount
        : roundMoney(((tax.percent || 0) / 100) * subtotal);
      return sum + (amount || 0);
    }, 0);
    return roundMoney(total);
  }, [taxes, subtotal]);
  const total = useMemo(() => roundMoney(subtotal + taxesAndChargesTotal), [subtotal, taxesAndChargesTotal]);

  const handleValidate = () => {
    const editedData: ExtractedData = {
      ...extractedData,
      items,
      taxes_or_charges: taxes,
      subtotal,
      grand_total: total,
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
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">Review & Edit Receipt</h2>
            {/* Validation Status Indicator */}
            {validationErrors ? (
              <div className="flex items-center gap-2 px-3 py-1 bg-red-50 border border-red-200 rounded-full">
                <AlertCircle className="h-4 w-4 text-red-500" />
                <span className="text-sm text-red-700 font-medium">Validation Failed</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1 bg-green-50 border border-green-200 rounded-full">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-700 font-medium">Validation Passed</span>
              </div>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Error Display */}
        {validationErrors && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <p className="text-sm text-red-700 font-medium">Validation Issues Found:</p>
            </div>
            <p className="text-sm text-red-600">{getErrorMessage()}</p>
            <p className="text-xs text-red-500 mt-2">Please review and correct the extracted data below before proceeding.</p>
          </div>
        )}

        {/* Success Display */}
        {!validationErrors && (
          <div className="mx-6 mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <p className="text-sm text-green-700 font-medium">Receipt Data Extracted Successfully!</p>
            </div>
            <p className="text-sm text-green-600">The receipt data has been automatically extracted and validated. Please review the details below and make any necessary adjustments before proceeding.</p>
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
                  onClick={() => {
                    const next = clamp(zoom - 0.25, 0.5, 3);
                    setZoom(next);
                    setPan(prev => clampPan(prev, next));
                  }}
                  className="p-1 hover:bg-gray-100 rounded"
                  type="button"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <button
                  onClick={() => {
                    const next = clamp(zoom + 0.25, 0.5, 3);
                    setZoom(next);
                    setPan(prev => clampPan(prev, next));
                  }}
                  className="p-1 hover:bg-gray-100 rounded"
                  type="button"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div
              ref={imageContainerRef}
              className="flex-1 overflow-hidden bg-gray-50 rounded cursor-grab active:cursor-grabbing select-none"
              style={{ overscrollBehavior: 'contain' }}
              onWheel={(e) => {
                e.preventDefault();
                const container = imageContainerRef.current;
                if (!container) return;
                if (containerSize.width <= 0 || containerSize.height <= 0) return;

                const rect = container.getBoundingClientRect();
                const cursorX = e.clientX - rect.left;
                const cursorY = e.clientY - rect.top;
                const cursorOffsetX = cursorX - containerSize.width / 2;
                const cursorOffsetY = cursorY - containerSize.height / 2;

                const nextZoom = clamp(zoom + (e.deltaY < 0 ? 0.15 : -0.15), 0.5, 3);

                // Keep the point under the cursor stable when zooming
                const pointX = (cursorOffsetX - pan.x) / zoom;
                const pointY = (cursorOffsetY - pan.y) / zoom;
                const nextPan = {
                  x: cursorOffsetX - nextZoom * pointX,
                  y: cursorOffsetY - nextZoom * pointY,
                };

                setZoom(nextZoom);
                setPan(clampPan(nextPan, nextZoom));
              }}
              onMouseDown={(e) => {
                if (e.button !== 0) return;
                panRef.current.isPanning = true;
                panRef.current.startX = e.clientX;
                panRef.current.startY = e.clientY;
                panRef.current.panX = pan.x;
                panRef.current.panY = pan.y;
              }}
              onMouseMove={(e) => {
                if (!panRef.current.isPanning) return;
                const dx = e.clientX - panRef.current.startX;
                const dy = e.clientY - panRef.current.startY;
                const candidate = { x: panRef.current.panX + dx, y: panRef.current.panY + dy };
                setPan(clampPan(candidate, zoom));
              }}
              onMouseUp={() => {
                panRef.current.isPanning = false;
              }}
              onMouseLeave={() => {
                panRef.current.isPanning = false;
              }}
            >
              <div className="w-full h-full flex items-center justify-center">
                <img
                  src={imageUrl}
                  alt="Receipt"
                  onLoad={(e) => {
                    const img = e.currentTarget;
                    setImageSize({ width: img.naturalWidth, height: img.naturalHeight });
                  }}
                  style={{
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                    transformOrigin: 'center center',
                  }}
                  className="max-w-none max-h-none"
                  draggable={false}
                />
              </div>
            </div>
          </div>

          {/* Right Panel - Editable Fields */}
          <div className="w-1/2 p-5 overflow-auto bg-white">
            {/* Items Section */}
            <div className="mb-7">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">Items</h3>
                <Button size="sm" variant="outline" onClick={handleAddItem} type="button">
                  <Plus className="h-4 w-4 mr-1" /> Add Item
                </Button>
              </div>
              <div className="grid grid-cols-12 gap-2 px-2 py-2 mb-2 text-[10px] uppercase tracking-wide text-gray-500 bg-white border border-gray-200 rounded-md">
                <div className="col-span-6">Item</div>
                <div className="col-span-2 text-right">Qty</div>
                <div className="col-span-2 text-right">Unit</div>
                <div className="col-span-2 text-right">Total</div>
              </div>
              <div className="space-y-2">
                {items.map((item, index) => (
                  <div
                    key={index}
                    className="relative grid grid-cols-12 gap-2 p-2 pr-10 bg-white border border-gray-200 rounded-md"
                  >
                    <input
                      type="text"
                      value={item.name}
                      onChange={(e) => handleItemChange(index, 'name', e.target.value)}
                      placeholder="Item name"
                      className="col-span-6 h-9 px-2 py-1 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(index, 'quantity', parseInt(e.target.value) || 0)}
                      placeholder="Qty"
                      className="col-span-2 h-9 self-center px-2 py-1 border rounded-md text-sm text-right focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <input
                      type="number"
                      step="0.01"
                      value={item.unit_price}
                      onChange={(e) => handleItemChange(index, 'unit_price', parseFloat(e.target.value) || 0)}
                      placeholder="Unit"
                      className="col-span-2 h-9 self-center px-2 py-1 border rounded-md text-sm text-right focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 appearance-none [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none [-moz-appearance:textfield]"
                    />
                    <input
                      type="number"
                      step="0.01"
                      value={item.total_price}
                      readOnly
                      tabIndex={-1}
                      aria-readonly="true"
                      className="col-span-2 h-9 self-center px-2 py-1 border rounded-md text-sm text-right bg-gray-50 text-gray-700 appearance-none [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none [-moz-appearance:textfield]"
                    />
                    <button
                      onClick={() => handleDeleteItem(index)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-red-500 hover:bg-red-50 rounded"
                      type="button"
                      aria-label="Delete item"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Taxes Section */}
            <div className="mb-7 pb-7 border-b">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">Taxes & Charges</h3>
                <Button size="sm" variant="outline" onClick={handleAddTax} type="button">
                  <Plus className="h-4 w-4 mr-1" /> Add Tax/Charge
                </Button>
              </div>
              <div className="space-y-2">
                {taxes.map((tax, index) => (
                  <div key={index} className="flex gap-2 items-center">
                    <input
                      type="text"
                      value={tax.name}
                      onChange={(e) => handleTaxChange(index, 'name', e.target.value)}
                      placeholder="Tax/Charge name"
                      className="flex-1 px-2 py-1 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <input
                      type="number"
                      step="0.01"
                      value={tax.amount}
                      onChange={(e) => handleTaxChange(index, 'amount', parseFloat(e.target.value) || 0)}
                      placeholder="Amount"
                      className="w-28 px-2 py-1 border rounded-md text-sm text-right focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                    <button
                      onClick={() => handleDeleteTax(index)}
                      className="p-1 text-red-500 hover:bg-red-50 rounded"
                      type="button"
                      aria-label="Delete tax or charge"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Totals Section */}
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900">Totals</h3>
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-gray-900">Total</label>
                <div className="w-36 px-3 py-2 border rounded-md text-sm font-semibold text-right bg-primary-50 border-primary-200 text-primary-800">
                  {total.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          <Button variant="outline" onClick={onClose} type="button">Cancel</Button>
          <Button onClick={handleValidate} type="button">
            {validationErrors ? 'Fix & Validate' : 'Confirm & Continue'}
          </Button>
        </div>
      </div>
    </div>
  );
};
