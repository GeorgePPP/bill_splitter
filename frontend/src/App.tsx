import React, { useState } from 'react';
import { Header } from '@/components/Layout/Header';
import { Footer } from '@/components/Layout/Footer';
import { Container } from '@/components/Layout/Container';
import { ReceiptUploader } from '@/components/BillSplitter/ReceiptUploader';
import { ItemAssignment } from '@/components/BillSplitter/ItemAssignment';
import { SplitSummary } from '@/components/BillSplitter/SplitSummary';
import { ParticipantManager } from '@/components/BillSplitter/ParticipantManager';
import { useBillSplitter } from '@/hooks/useBillSplitter';
import { useReceiptOCR } from '@/hooks/useReceiptOCR';
import { usePersonManager } from '@/hooks/usePersonManager';
import { useItemAssignment, ItemSplit } from '@/hooks/useItemAssignment';
import { useCalculations } from '@/hooks/useCalculations';
import { receiptService } from '@/services/receiptService';
import { splitService } from '@/services/splitService';
import { Person } from '@/types/person.types';
import { ReceiptData } from '@/types/bill.types';

const App: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  const billSplitter = useBillSplitter();
  const receiptOCR = useReceiptOCR();
  const personManager = usePersonManager();
  const itemAssignment = useItemAssignment();
  const calculations = useCalculations();

  const handleReceiptUpload = async (file: File) => {
    try {
      billSplitter.actions.setLoading(true);
      console.log('[App] Starting receipt upload for file:', file.name);
      
      // Upload receipt
      const uploadResponse = await receiptOCR.actions.uploadReceipt(file);
      console.log('[App] Upload response:', uploadResponse);
      
      if (uploadResponse.receipt_id) {
        // Process receipt - validation errors will be caught and set in state
        try {
          const processResponse = await receiptOCR.actions.processReceipt(uploadResponse.receipt_id);
          console.log('[App] Process response:', processResponse);
          
          if (processResponse.processed_data) {
            billSplitter.actions.setReceiptData(processResponse.processed_data, uploadResponse.receipt_id);
            itemAssignment.actions.initializeAssignments(processResponse.processed_data.items);
            billSplitter.actions.nextStep();
          }
        } catch (error) {
          const apiError = error as any;
          console.log('[App] Process error:', {
            status: apiError.status,
            message: apiError.message,
            details: apiError.details,
            needsValidation: receiptOCR.state.needsValidation
          });
          
          // If validation error (422), the modal will show automatically
          // The state is already set in useReceiptOCR hook
          if (apiError.status !== 422) {
            billSplitter.actions.setError('Failed to process receipt. Please try again.');
          }
        }
      }
    } catch (error) {
      console.error('[App] Error processing receipt:', error);
      billSplitter.actions.setError('Failed to upload receipt. Please try again.');
    } finally {
      billSplitter.actions.setLoading(false);
    }
  };
  
  // Add this new function:
  
  const handleValidationCorrection = async (correctedData: any) => {
    try {
      billSplitter.actions.setLoading(true);
      
      if (receiptOCR.state.receiptId) {
        const processResponse = await receiptOCR.actions.reprocessWithCorrectedData(
          receiptOCR.state.receiptId,
          correctedData
        );
        
        if (processResponse.processed_data) {
          billSplitter.actions.setReceiptData(processResponse.processed_data, receiptOCR.state.receiptId);
          itemAssignment.actions.initializeAssignments(processResponse.processed_data.items);
          billSplitter.actions.nextStep();
        }
      }
    } catch (error) {
      const apiError = error as any;
      // If still validation error, modal stays open with new errors
      if (apiError.status !== 422) {
        billSplitter.actions.setError('Failed to validate receipt. Please try again.');
      }
    } finally {
      billSplitter.actions.setLoading(false);
    }
  };

  const handleMultipleAssignItemToMultiplePeople = (itemIndex: number, personIds: string[]) => {
    // This will trigger the split choice modal
    itemAssignment.actions.assignItemToMultiplePeople(itemIndex, personIds, 'equal');
  };

  const handleReceiptProcessed = async () => {
    // This is called when the user clicks "Process Receipt" button
    // The actual processing happens in handleReceiptUpload
  };

  const handleAssignItem = (itemIndex: number, personId: string) => {
    return itemAssignment.actions.assignItem(itemIndex, personId, billSplitter.state.participants);
  };

  const handleAssignItemToMultiplePeople = (itemIndex: number, personIds: string[], splitType: 'equal' | 'unequal', customSplits?: ItemSplit[]) => {
    itemAssignment.actions.assignItemToMultiplePeople(itemIndex, personIds, splitType, customSplits);
  };

  const handleConfirmAssignment = () => {
    itemAssignment.actions.confirmPendingAssignment();
  };

  const handleCancelAssignment = () => {
    itemAssignment.actions.cancelPendingAssignment();
  };

  const handleRemovePersonFromSplit = (itemIndex: number, personId: string) => {
    itemAssignment.actions.removePersonFromSplit(itemIndex, personId);
  };

  const handleCloseSplitModal = () => {
    itemAssignment.actions.closeSplitModal();
  };

  const handleCalculateSplit = async () => {
    try {
      billSplitter.actions.setLoading(true);
      
      // Calculate split using the calculations hook
      const personSplits = calculations.actions.calculateSplit(
        billSplitter.state.participants,
        itemAssignment.state.assignments,
        billSplitter.state.receiptData!,
        'proportional'
      );
      
      billSplitter.actions.setSplitResults(personSplits);
      billSplitter.actions.nextStep();
    } catch (error) {
      console.error('Error calculating split:', error);
      billSplitter.actions.setError('Failed to calculate split. Please try again.');
    } finally {
      billSplitter.actions.setLoading(false);
    }
  };

  const handleStartOver = () => {
    billSplitter.actions.reset();
    receiptOCR.actions.reset();
    personManager.actions.reset();
    itemAssignment.actions.reset();
    calculations.actions.reset();
  };

  const handleShare = () => {
    // Implement sharing functionality
    console.log('Share results');
  };

  const handleDownload = () => {
    // Implement download functionality
    console.log('Download results');
  };

  const renderStep = () => {
    switch (billSplitter.state.currentStep) {
      case 1:
        return (
          <ParticipantManager
            participants={billSplitter.state.participants}
            onParticipantsChange={billSplitter.actions.setParticipants}
            onNext={billSplitter.actions.nextStep}
            disabled={billSplitter.state.isLoading}
          />
        );
      
      case 2:
        return (
          <ReceiptUploader
            onReceiptUploaded={handleReceiptUpload}
            onReceiptProcessed={handleReceiptProcessed}
            onValidationCorrection={handleValidationCorrection}
            isLoading={receiptOCR.state.isUploading || receiptOCR.state.isProcessing}
            uploadProgress={receiptOCR.state.uploadProgress}
            error={receiptOCR.state.error}
            validationError={receiptOCR.state.validationError}
            needsValidation={receiptOCR.state.needsValidation}
            extractedData={receiptOCR.state.extractedData}
            disabled={billSplitter.state.isLoading}
          />
        );
      
        case 3:
          return (
            <ItemAssignment
              items={billSplitter.state.receiptData?.items || []}
              participants={billSplitter.state.participants}
              assignments={itemAssignment.state.assignments}
              onAssignItem={handleAssignItem}
              onAssignItemToMultiplePeople={handleAssignItemToMultiplePeople}
              onConfirmAssignment={handleConfirmAssignment}
              onCancelAssignment={handleCancelAssignment}
              onUnassignItem={itemAssignment.actions.unassignItem}
              onRemovePersonFromSplit={handleRemovePersonFromSplit}
              onCloseSplitModal={handleCloseSplitModal}
              onNext={handleCalculateSplit}
              onBack={billSplitter.actions.prevStep}
              disabled={billSplitter.state.isLoading}
              pendingAssignment={itemAssignment.state.pendingAssignment}
              pendingSplitModal={itemAssignment.state.pendingSplitModal}
            />
          );
      
      case 4:
        return (
          <SplitSummary
            personSplits={calculations.state.personSplits}
            totalBill={calculations.state.totalBill}
            totalTax={calculations.state.totalTax}
            totalServiceCharge={calculations.state.totalServiceCharge}
            totalDiscount={calculations.state.totalDiscount}
            onStartOver={handleStartOver}
            onShare={handleShare}
            onDownload={handleDownload}
            disabled={billSplitter.state.isLoading}
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        onMenuToggle={() => setIsMenuOpen(!isMenuOpen)}
        isMenuOpen={isMenuOpen}
      />
      
      <main className="flex-1 py-8">
        <Container>
          {billSplitter.state.error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <div className="text-red-500">⚠️</div>
                <p className="text-red-700">{billSplitter.state.error}</p>
                <button
                  onClick={() => billSplitter.actions.setError(null)}
                  className="ml-auto text-red-500 hover:text-red-700"
                >
                  ✕
                </button>
              </div>
            </div>
          )}
          
          {renderStep()}
        </Container>
      </main>
      
      <Footer />
    </div>
  );
};

export default App;