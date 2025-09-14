/**
 * FileUpload Component
 * 
 * A React component to handle document uploads for compliance analysis.
 * Manages file selection state and handles the analysis workflow.
 */

import React, { useState } from 'react';
import axios from 'axios';

const FileUpload = ({ setIsLoading, setAnalysisResult }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);

  // Handle file selection from input
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    setError(null);
  };

  // Handle drag and drop events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setError(null);
    }
  };

  // Handle document analysis
  const handleAnalyze = async () => {
    // Check if a file is selected
    if (!selectedFile) {
      setError('Please select a file before analyzing.');
      return;
    }

    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Please select a PDF or DOCX file.');
      return;
    }

    try {
      // Set loading state to true
      setIsLoading(true);
      setError(null);

      // Create FormData object and append the selected file
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Send POST request to backend endpoint
      const response = await axios.post(
        'http://localhost:8000/analyze-document',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000, // 2 minute timeout for analysis
        }
      );

      // On success, update parent's state with analysis result
      if (response.data && response.data.success) {
        console.log('Analysis response received:', response.data);
        console.log('Score data:', response.data.compliance_analysis?.score);
        console.log('Findings data:', response.data.compliance_analysis?.findings);
        
        // IMPORTANT: Save analysis to database for history tracking
        try {
          console.log('Saving analysis to database...');
          const saveResponse = await axios.post(
            'http://localhost:8000/save-analysis-result',
            response.data,
            {
              headers: {
                'Content-Type': 'application/json',
              },
            }
          );
          
          if (saveResponse.data && saveResponse.data.success) {
            console.log('✅ Analysis saved to database with ID:', saveResponse.data.document_id);
            
            // Add document ID to the response data
            const enrichedData = {
              ...response.data,
              document_id: saveResponse.data.document_id
            };
            setAnalysisResult(enrichedData);
          } else {
            console.warn('⚠️ Analysis completed but not saved to database');
            setAnalysisResult(response.data);
          }
        } catch (saveError) {
          console.error('❌ Error saving analysis to database:', saveError);
          // Still show the analysis results even if saving fails
          setAnalysisResult(response.data);
        }
      } else {
        console.error('Analysis response missing success flag:', response.data);
        throw new Error(response.data?.error || 'Analysis failed');
      }

    } catch (error) {
      // Handle errors
      console.error('Analysis error:', error);
      
      let errorMessage = 'An error occurred during analysis.';
      if (error.response) {
        errorMessage = error.response.data?.detail || error.response.data?.error || errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
    } finally {
      // Set loading state back to false
      setIsLoading(false);
    }
  };

  // Clear selected file
  const clearFile = () => {
    setSelectedFile(null);
    setError(null);
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-8">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Upload Document for Analysis
        </h2>
        <p className="text-gray-600">
          Upload your healthcare compliance document for AI-powered analysis
        </p>
      </div>

      {/* File Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-200 ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : selectedFile
            ? 'border-green-500 bg-green-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          // File selected state
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <div className="bg-green-100 rounded-full p-3">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div>
              <p className="text-lg font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-gray-500">{formatFileSize(selectedFile.size)}</p>
            </div>
            <button
              onClick={clearFile}
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              Remove file
            </button>
          </div>
        ) : (
          // No file selected state
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <div className="bg-gray-100 rounded-full p-3">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
            </div>
            <div>
              <p className="text-lg font-medium text-gray-900">
                Drop your document here
              </p>
              <p className="text-gray-500">
                or click to browse files
              </p>
            </div>
            <p className="text-sm text-gray-400">
              Supports PDF and DOCX files (max 50MB)
            </p>
          </div>
        )}

        {/* Hidden file input */}
        <input
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.docx"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Analyze button */}
      <div className="mt-6">
        <button
          onClick={handleAnalyze}
          disabled={!selectedFile}
          className={`w-full py-3 px-6 rounded-lg font-medium text-white transition-colors duration-200 ${
            selectedFile
              ? 'bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:ring-blue-200'
              : 'bg-gray-300 cursor-not-allowed'
          }`}
        >
          Analyze Document
        </button>
      </div>

      {/* Supported formats info */}
      <div className="mt-6 text-center">
        <p className="text-xs text-gray-500">
          Supported formats: PDF, DOCX • Maximum file size: 50MB
        </p>
      </div>
    </div>
  );
};

export default FileUpload;