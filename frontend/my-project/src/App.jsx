/**
 * The enhanced main application component with comprehensive compliance management features.
 * Includes document analysis, history tracking, and advanced rule management.
 */

import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ScoreCard from './components/ScoreCard';
import FindingCard from './components/FindingCard';
import RuleEditor from './components/RuleEditor';
import DocumentHistory from './components/DocumentHistory';
import EnhancedRuleEditor from './components/EnhancedRuleEditor';
import './App.css';

function App() {
  // Primary application state
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('analyze');

  // Reset function to start a new analysis
  const resetAnalysis = () => {
    setAnalysisResult(null);
    setError('');
  };

  // Re-analyze with custom rules function
  const reanalyzeWithCustomRules = async () => {
    if (!analysisResult?.document_id) {
      setError('No document ID available for re-analysis');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      
      // Note: For re-analysis, we would need the original file
      // For now, we'll show a message about this limitation
      setError('Re-analysis feature requires the original file to be re-uploaded. Please go to Rule Management tab to add document-specific rules, then upload the document again for analysis with custom rules.');
      
    } catch (error) {
      setError('Failed to re-analyze document with custom rules');
    } finally {
      setIsLoading(false);
    }
  };

  // Navigation tabs configuration
  const tabs = [
    { 
      id: 'analyze', 
      name: 'Document Analysis', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    },
    { 
      id: 'history', 
      name: 'Document History', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    { 
      id: 'rules', 
      name: 'Rule Management', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                CompliAI Linter
              </h1>
              <p className="text-gray-600 mt-1">
                Comprehensive Healthcare Compliance Management Platform
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {isLoading && (
                <>
                  <span className="text-sm text-blue-600">
                    Analyzing Document...
                  </span>
                  <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
                </>
              )}
              {analysisResult && !isLoading && activeTab === 'analyze' && (
                <>
                  <span className="text-sm text-green-600">
                    Analysis Complete
                  </span>
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                </>
              )}
              {!analysisResult && !isLoading && activeTab === 'analyze' && (
                <>
                  <span className="text-sm text-gray-500">
                    Ready to Analyze
                  </span>
                  <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                </>
              )}
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className={`mr-2 ${activeTab === tab.id ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'}`}>
                    {tab.icon}
                  </span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Tab Content */}
        {activeTab === 'analyze' && (
          <>
            {/* Loading State */}
            {isLoading && (
              <div className="text-center py-12">
                <div className="inline-flex items-center px-6 py-4 bg-blue-50 rounded-lg border border-blue-200">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <div className="text-left">
                    <p className="text-blue-800 font-medium">Analyzing your document...</p>
                    <p className="text-blue-600 text-sm">This may take a few moments depending on document size.</p>
                  </div>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-red-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <h3 className="text-red-800 font-medium">Analysis Error</h3>
                    <p className="text-red-700 text-sm mt-1">{error}</p>
                    <button 
                      onClick={() => setError('')}
                      className="text-red-600 text-sm underline mt-2 hover:text-red-800"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Analysis Results State */}
            {analysisResult && !isLoading && (
              <div className="space-y-8">
                {/* Debug info - remove in production */}
                {console.log('Rendering analysis result:', analysisResult)}
                
                {/* Action Buttons */}
                <div className="text-center space-x-4">
                  <button
                    onClick={resetAnalysis}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Analyze New Document
                  </button>
                  
                  {analysisResult.document_id && (
                    <button
                      onClick={() => setActiveTab('rules')}
                      className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors duration-200"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Add Document Rules
                    </button>
                  )}
                </div>

                {/* Dashboard Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  
                  {/* Left Column - Score Card */}
                  <div className="lg:col-span-1">
                    <div className="bg-white rounded-lg shadow-sm p-6">
                      <ScoreCard 
                        score={analysisResult.compliance_analysis?.score?.score || 0} 
                        label="Compliance Score"
                      />
                      
                      {/* Quick Stats */}
                      <div className="mt-8 border-t pt-6">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">
                          Analysis Summary
                        </h3>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Findings:</span>
                            <span className="font-semibold">
                              {analysisResult.compliance_analysis?.findings?.length || 0}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Critical Issues:</span>
                            <span className="font-semibold text-red-600">
                              {analysisResult.compliance_analysis?.findings?.filter(f => f.severity === 'Critical').length || 0}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Major Issues:</span>
                            <span className="font-semibold text-orange-600">
                              {analysisResult.compliance_analysis?.findings?.filter(f => f.severity === 'Major').length || 0}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Minor Issues:</span>
                            <span className="font-semibold text-yellow-600">
                              {analysisResult.compliance_analysis?.findings?.filter(f => f.severity === 'Minor').length || 0}
                            </span>
                          </div>
                        </div>

                        {/* File Information */}
                        {analysisResult.file_info && (
                          <div className="mt-6 pt-4 border-t border-gray-200">
                            <h4 className="text-sm font-medium text-gray-900 mb-2">
                              Document Details
                            </h4>
                            <div className="space-y-1 text-xs text-gray-600">
                              <p><strong>File:</strong> {analysisResult.file_info.filename}</p>
                              <p><strong>Type:</strong> {analysisResult.file_info.file_type}</p>
                              <p><strong>Size:</strong> {Math.round(analysisResult.file_info.file_size / 1024)} KB</p>
                              {analysisResult.file_info.sections_found && (
                                <p><strong>Sections:</strong> {analysisResult.file_info.sections_found}</p>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right Column - Findings List */}
                  <div className="lg:col-span-2">
                    <div className="bg-white rounded-lg shadow-sm">
                      <div className="px-6 py-4 border-b border-gray-200">
                        <h2 className="text-2xl font-bold text-gray-900">
                          Compliance Findings
                        </h2>
                        <p className="text-gray-600 mt-1">
                          Detailed analysis of compliance issues found in your document
                        </p>
                      </div>
                      
                      <div className="p-6">
                        {analysisResult.compliance_analysis?.findings && analysisResult.compliance_analysis.findings.length > 0 ? (
                          <div className="space-y-4">
                            {analysisResult.compliance_analysis.findings.map((finding, index) => (
                              <FindingCard 
                                key={index} 
                                finding={finding} 
                              />
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-12">
                            <div className="text-green-400 text-6xl mb-4">
                              ✅
                            </div>
                            <div className="text-green-600 text-lg mb-2 font-medium">
                              No compliance issues found!
                            </div>
                            <p className="text-gray-600">
                              Your document meets all compliance requirements.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Welcome/Ready State */}
            {!analysisResult && !isLoading && !error && (
              <div className="space-y-8">
                {/* Welcome Message */}
                <div className="text-center py-12">
                  <div className="max-w-3xl mx-auto">
                    <h2 className="text-3xl font-bold text-gray-900 mb-4">
                      Welcome to CompliAI Linter
                    </h2>
                    <p className="text-xl text-gray-600 mb-8">
                      Upload your healthcare compliance documents for AI-powered analysis. 
                      Get instant feedback on regulatory compliance, missing sections, and improvement recommendations.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                      <div className="text-center p-6">
                        <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2">Upload Documents</h3>
                        <p className="text-gray-600 text-sm">Support for PDF and DOCX files</p>
                      </div>
                      <div className="text-center p-6">
                        <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2">AI Analysis</h3>
                        <p className="text-gray-600 text-sm">Comprehensive compliance checking</p>
                      </div>
                      <div className="text-center p-6">
                        <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2">Instant Results</h3>
                        <p className="text-gray-600 text-sm">Detailed findings and recommendations</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* File Upload Component */}
                <FileUpload 
                  setAnalysisResult={setAnalysisResult}
                  setIsLoading={setIsLoading}
                  setError={setError}
                />

                {/* Legacy Rule Editor Component (kept for backwards compatibility) */}
                <div className="mt-8">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <div className="flex items-start">
                      <svg className="w-5 h-5 text-blue-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <h3 className="text-blue-800 font-medium">Legacy Rule Editor</h3>
                        <p className="text-blue-700 text-sm mt-1">
                          This is the basic rule editor. For advanced features including document-specific rules and enhanced management, 
                          switch to the "Rule Management" tab above.
                        </p>
                      </div>
                    </div>
                  </div>
                  <RuleEditor />
                </div>
              </div>
            )}
          </>
        )}

        {/* Document History Tab */}
        {activeTab === 'history' && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Document History Dashboard
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Track all your analyzed documents with comprehensive compliance scores, 
                detailed findings breakdown, and complete audit trail for regulatory compliance.
              </p>
            </div>
            <DocumentHistory />
          </div>
        )}

        {/* Enhanced Rule Management Tab */}
        {activeTab === 'rules' && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Advanced Rule Management
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Manage global compliance rules and document-specific requirements. 
                Create custom rules with severity levels for comprehensive compliance checking.
              </p>
              {analysisResult?.document_id && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg max-w-md mx-auto">
                  <p className="text-blue-800 text-sm">
                    <strong>📄 Document Context Available:</strong> You can now create document-specific rules for the analyzed document.
                  </p>
                </div>
              )}
            </div>
            <EnhancedRuleEditor documentId={analysisResult?.document_id || null} />
          </div>
        )}

        {/* Footer */}
        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>
            Powered by CompliAI Linter - Comprehensive Healthcare Compliance Management Platform
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
