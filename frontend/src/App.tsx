import React, { useState, useEffect } from 'react';
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
import { useSession } from '@/hooks/useSession';
import { useValidationModal } from '@/hooks/useValidationModal';
import { ReceiptValidationModal } from '@/components/BillSplitter/ReceiptValidationModal';

const App: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  // Initialize session first
  const session = useSession();
  
  // Initialize other hooks with session actions
  const billSplitter = useBillSplitter({
    saveParticipants: session.actions.saveParticipants,
    saveReceiptData: session.actions.saveReceiptData,
    saveSplitResults: session.actions.saveSplitResults,
    saveOcrText: session.actions.saveOcrText,
  });
  const receiptOCR = useReceiptOCR();
  const personManager = usePersonManager();
  const itemAssignment = useItemAssignment();
  const calculations = useCalculations();
  const validationModal = useValidationModal();

  // Create session on app start
  useEffect(() => {
    if (session.state.isInitialized && !session.state.sessionToken && !session.state.hasExistingSession) {
      session.actions.createNewSession().catch(error => {
        console.error('Failed to create session on startup:', error);
        // Continue without session - app will still work
      });
    }
  }, [session.state.isInitialized, session.state.sessionToken, session.state.hasExistingSession, session.actions]);

  // Restore session data if available
  useEffect(() => {
    const restoreSessionData = async () => {
      if (session.state.hasExistingSession && session.state.sessionData) {
        console.log('Restoring session data...');
        const restoredData = await session.actions.restoreSession();
        
        if (restoredData) {
          // Restore bill splitter state
          billSplitter.actions.restoreState(restoredData);
          
          // If receipt data exists, restore validation modal state
          if (restoredData.receiptData) {
            validationModal.actions.updateExtractedData(restoredData.receiptData);
            validationModal.actions.markAsValidated(restoredData.receiptData);
            
            // Initialize item assignments
            itemAssignment.actions.initializeAssignments(restoredData.receiptData.items);
            // Item assignments will be restored through billSplitter.actions.restoreState
          }
          
          console.log('Session data restored successfully');
        }
      }
    };

    restoreSessionData().catch(error => {
      console.error('Failed to restore session data:', error);
    });
  }, [session.state.hasExistingSession, session.state.sessionData, billSplitter.actions, validationModal.actions, itemAssignment.actions, session.actions]);

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
          
          // Save OCR text immediately (expensive to reprocess)
          if (processResponse.ocr_text) {
            session.actions.saveOcrText?.(processResponse.ocr_text);
          }
          
          if (processResponse.processed_data) {
            // Set receipt data without auto-saving to session (to reduce DB calls)
            console.log('[App] Setting receipt data without auto-save');
            billSplitter.actions.setReceiptData(processResponse.processed_data, uploadResponse.receipt_id, false);
            itemAssignment.actions.initializeAssignments(processResponse.processed_data.items);
            
            // Store validation modal state globally
            const imagePreview = URL.createObjectURL(file);
            validationModal.actions.openModal(
              imagePreview,
              processResponse.processed_data,
              null,
              processResponse.ocr_text
            );
            
            // Don't auto-advance to next step - let validation modal handle the flow
          }
        } catch (error) {
          const apiError = error as any;
          console.log('[App] Process error:', {
            status: apiError.status,
            message: apiError.message,
            details: apiError.details,
            needsValidation: receiptOCR.state.needsValidation
          });
          
          // Save OCR text even if processing failed
          if (apiError.ocr_text) {
            session.actions.saveOcrText?.(apiError.ocr_text);
          }
          
          // If validation error (422), show validation modal with error data
          if (apiError.status === 422 && apiError.extracted_data) {
            const imagePreview = URL.createObjectURL(file);
            validationModal.actions.openModal(
              imagePreview,
              apiError.extracted_data,
              apiError.details,
              apiError.ocr_text
            );
          } else {
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
      
      if (billSplitter.state.receiptId) {
        // Save corrected data to session immediately (expensive to reprocess)
        console.log('[App] Saving corrected receipt data to session');
        session.actions.saveReceiptData?.(correctedData, billSplitter.state.receiptId);
        
        // Check if this is the initial validation (no changes made) or reprocessing
        const hasChanges = JSON.stringify(correctedData) !== JSON.stringify(receiptOCR.state.extractedData);
        
        if (hasChanges) {
          // User made changes, reprocess with corrected data
          const processResponse = await receiptOCR.actions.reprocessWithCorrectedData(
            billSplitter.state.receiptId,
            correctedData
          );
          
          if (processResponse.processed_data) {
            billSplitter.actions.setReceiptData(processResponse.processed_data, billSplitter.state.receiptId, false);
            itemAssignment.actions.initializeAssignments(processResponse.processed_data.items);
            
            // Mark as validated in global state
            validationModal.actions.markAsValidated(processResponse.processed_data);
            validationModal.actions.closeModal();
            
            // Always go to assignment page (step 3) after validation
            billSplitter.actions.goToStep(3);
          }
        } else {
          // No changes made, just proceed with existing data
          if (receiptOCR.state.processedData) {
            billSplitter.actions.setReceiptData(receiptOCR.state.processedData, billSplitter.state.receiptId, false);
            itemAssignment.actions.initializeAssignments(receiptOCR.state.processedData.items);
            
            // Mark as validated in global state
            validationModal.actions.markAsValidated(receiptOCR.state.processedData);
            validationModal.actions.closeModal();
          }
          // Always go to assignment page (step 3) after validation
          billSplitter.actions.goToStep(3);
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
    // Reset all state and go back to step 1
    billSplitter.actions.reset();
    receiptOCR.actions.reset();
    personManager.actions.reset();
    itemAssignment.actions.reset();
    calculations.actions.reset();
    validationModal.actions.reset();
    // Session and known participants are preserved automatically
    console.log('Starting over - known participants preserved:', session.actions.getKnownParticipants().length);
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
            knownParticipants={session.actions.getKnownParticipants()}
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
            onModifyAssignment={() => billSplitter.actions.goToStep(3)}
            onShare={handleShare}
            onDownload={handleDownload}
            disabled={billSplitter.state.isLoading}
          />
        );
      
      default:
        return null;
    }
  };

  // Show loading while session is initializing
  if (!session.state.isInitialized) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        onMenuToggle={() => setIsMenuOpen(!isMenuOpen)}
        isMenuOpen={isMenuOpen}
      />
      
      <main className="flex-1 py-8">
        <Container>
          {/* Session Error */}
          {session.state.error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <div className="text-red-500">⚠️</div>
                <p className="text-red-700">{session.state.error}</p>
                <button
                  onClick={() => session.actions.createNewSession()}
                  className="ml-auto text-red-500 hover:text-red-700"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* Bill Splitter Error */}
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

          {/* Validation Status Indicator - Only show in Assignment page (step 3) */}
          {validationModal.state.hasValidatedData && billSplitter.state.currentStep === 3 && (
            <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="text-green-500">✓</div>
                  <p className="text-green-700 text-sm">Receipt data has been validated</p>
                </div>
                {validationModal.actions.canReopenModal() && (
                  <button
                    onClick={validationModal.actions.reopenModal}
                    className="text-green-600 hover:text-green-800 text-sm font-medium"
                  >
                    Revalidate Receipt Data
                  </button>
                )}
              </div>
            </div>
          )}
          
          {renderStep()}
        </Container>
      </main>
      
      {/* Global Validation Modal - Now acts as a "page" */}
      {validationModal.state.isOpen && validationModal.state.imageUrl && validationModal.state.extractedData && (
        <ReceiptValidationModal
          isOpen={validationModal.state.isOpen}
          onClose={() => {}} // Don't allow closing without validation - this is now a "page"
          imageUrl={validationModal.state.imageUrl}
          extractedData={validationModal.state.extractedData}
          validationErrors={validationModal.state.validationErrors}
          onValidate={handleValidationCorrection}
        />
      )}
      
      <Footer />
    </div>
  );
};

export default App;