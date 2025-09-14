/**
 * DocumentHistory Component
 * 
 * A React component for viewing and managing document analysis history.
 * Displays a list of previously analyzed documents with their compliance scores and findings.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DocumentHistory = () => {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDocumentHistory();
  }, []);

  const fetchDocumentHistory = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const response = await axios.get('http://localhost:8000/document-history');
      
      if (response.data && response.data.success) {
        setDocuments(response.data.documents || []);
      } else {
        setError('Failed to load document history');
      }
    } catch (error) {
      console.error('Error fetching document history:', error);
      setError('Failed to load document history. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const viewDocumentDetails = async (documentId) => {
    try {
      setError('');
      const response = await axios.get(`http://localhost:8000/document-details/${documentId}`);
      
      if (response.data && response.data.success) {
        setSelectedDocument(response.data.analysis_result);
        setShowDetails(true);
      } else {
        setError('Failed to load document details');
      }
    } catch (error) {
      console.error('Error fetching document details:', error);
      setError('Failed to load document details. Please try again.');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600 bg-green-100 border-green-200';
    if (score >= 75) return 'text-blue-600 bg-blue-100 border-blue-200';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100 border-yellow-200';
    if (score >= 40) return 'text-orange-600 bg-orange-100 border-orange-200';
    return 'text-red-600 bg-red-100 border-red-200';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Document History
            </h2>
            <p className="text-gray-600">
              View and manage your previous document analyses and compliance reports.
            </p>
          </div>
          <button
            onClick={fetchDocumentHistory}
            disabled={isLoading}
            className="px-4 py-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors border border-blue-200"
          >
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <div className="text-center py-12">
          <svg className="animate-spin h-8 w-8 text-gray-400 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-gray-500">Loading document history...</p>
        </div>
      ) : documents.length > 0 ? (
        <div className="space-y-4">
          {documents.map((doc) => (
            <div key={doc.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-3">
                    <h3 className="text-lg font-medium text-gray-900">{doc.filename}</h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getScoreColor(doc.compliance_score)}`}>
                      {doc.compliance_score}/100
                    </span>
                    <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {doc.file_type}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-6 text-sm text-gray-600 mb-3">
                    <span>
                      <strong>Upload Date:</strong> {new Date(doc.upload_date).toLocaleDateString()}
                    </span>
                    <span>
                      <strong>File Size:</strong> {formatFileSize(doc.file_size)}
                    </span>
                    <span>
                      <strong>Total Findings:</strong> {doc.total_findings}
                    </span>
                  </div>

                  {/* Findings Breakdown */}
                  <div className="flex items-center gap-4 text-sm">
                    {doc.critical_findings > 0 && (
                      <span className="text-red-600 bg-red-50 px-2 py-1 rounded">
                        Critical: {doc.critical_findings}
                      </span>
                    )}
                    {doc.major_findings > 0 && (
                      <span className="text-orange-600 bg-orange-50 px-2 py-1 rounded">
                        Major: {doc.major_findings}
                      </span>
                    )}
                    {doc.minor_findings > 0 && (
                      <span className="text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
                        Minor: {doc.minor_findings}
                      </span>
                    )}
                    {doc.total_findings === 0 && (
                      <span className="text-green-600 bg-green-50 px-2 py-1 rounded">
                        No Issues Found
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => viewDocumentDetails(doc.id)}
                    className="px-4 py-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors border border-blue-200"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-500 mb-2">No document history found</p>
          <p className="text-gray-400 text-sm">Upload and analyze your first document to see history</p>
        </div>
      )}

      {/* Document Details Modal */}
      {showDetails && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">Document Analysis Details</h3>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-500 hover:text-gray-700 p-2 hover:bg-gray-100 rounded-lg"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Display detailed analysis results */}
            <div className="space-y-6">
              {/* File Information */}
              <div className="grid grid-cols-2 gap-6 p-4 bg-gray-50 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">File Information</h4>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p><strong>Filename:</strong> {selectedDocument.file_info?.filename}</p>
                    <p><strong>Type:</strong> {selectedDocument.file_info?.file_type}</p>
                    <p><strong>Size:</strong> {formatFileSize(selectedDocument.file_info?.file_size || 0)}</p>
                    <p><strong>Sections:</strong> {selectedDocument.file_info?.sections_found || 0}</p>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Compliance Score</h4>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p><strong>Score:</strong> {selectedDocument.compliance_analysis?.score?.score}/100</p>
                    <p><strong>Level:</strong> {selectedDocument.compliance_analysis?.score?.compliance_level}</p>
                    <p><strong>Total Findings:</strong> {selectedDocument.compliance_analysis?.findings?.length || 0}</p>
                  </div>
                </div>
              </div>

              {/* Findings List */}
              {selectedDocument.compliance_analysis?.findings && selectedDocument.compliance_analysis.findings.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-4">Compliance Findings</h4>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {selectedDocument.compliance_analysis.findings.map((finding, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-3">
                        <div className="flex items-start gap-3">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            finding.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                            finding.severity === 'Major' ? 'bg-orange-100 text-orange-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {finding.severity}
                          </span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">{finding.title || finding.description}</p>
                            {finding.explanation && (
                              <p className="text-xs text-gray-600 mt-1">{finding.explanation}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentHistory;