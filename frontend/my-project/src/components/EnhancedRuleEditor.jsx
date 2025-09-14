/**
 * EnhancedRuleEditor Component
 * 
 * A React component for managing both global and document-specific compliance rules.
 * Provides tabbed interface for different rule scopes and comprehensive rule management.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const EnhancedRuleEditor = ({ documentId = null }) => {
  const [activeTab, setActiveTab] = useState('global');
  const [newRuleText, setNewRuleText] = useState('');
  const [severity, setSeverity] = useState('Major');
  const [globalRules, setGlobalRules] = useState([]);
  const [documentRules, setDocumentRules] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchGlobalRules();
    if (documentId) {
      fetchDocumentRules();
    }
  }, [documentId]);

  const fetchGlobalRules = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('http://127.0.0.1:8000/get-rules/');
      if (response.data && response.data.success) {
        setGlobalRules(response.data.rules || []);
      }
    } catch (error) {
      console.error('Error fetching global rules:', error);
      setError('Failed to load global rules');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDocumentRules = async () => {
    if (!documentId) return;
    
    try {
      const response = await axios.get(`http://127.0.0.1:8000/document-rules/${documentId}`);
      if (response.data && response.data.success) {
        setDocumentRules(response.data.rules || []);
      }
    } catch (error) {
      console.error('Error fetching document rules:', error);
      if (error.response?.status !== 404) {
        setError('Failed to load document-specific rules');
      }
    }
  };

  const handleSaveRule = async () => {
    if (!newRuleText.trim()) {
      setError('Please enter a rule description before saving.');
      return;
    }

    if (activeTab === 'document' && !documentId) {
      setError('Document ID is required for document-specific rules.');
      return;
    }

    try {
      setIsSaving(true);
      setError('');
      setSuccessMessage('');

      const endpoint = activeTab === 'global' 
        ? 'http://127.0.0.1:8000/add-rule/'
        : `http://127.0.0.1:8000/add-document-rule/${documentId}`;

      const response = await axios.post(endpoint, {
        rule_text: newRuleText.trim(),
        rule_type: 'Custom',
        severity: severity
      });

      if (response.data && response.data.success) {
        setNewRuleText('');
        setSuccessMessage(`${activeTab === 'global' ? 'Global' : 'Document-specific'} rule saved successfully!`);
        
        if (activeTab === 'global') {
          await fetchGlobalRules();
        } else {
          await fetchDocumentRules();
        }
        
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        throw new Error(response.data?.error || 'Failed to save rule');
      }
    } catch (error) {
      console.error('Error saving rule:', error);
      let errorMessage = 'Failed to save rule. Please try again.';
      if (error.response) {
        errorMessage = error.response.data?.detail || error.response.data?.error || errorMessage;
      }
      setError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteRule = async (ruleId, isGlobal = true) => {
    if (!window.confirm('Are you sure you want to delete this rule?')) {
      return;
    }

    try {
      const endpoint = isGlobal 
        ? `http://127.0.0.1:8000/delete-rule/${ruleId}`
        : `http://127.0.0.1:8000/delete-document-rule/${ruleId}`;

      const response = await axios.delete(endpoint);
      
      if (response.data && response.data.success) {
        setSuccessMessage('Rule deleted successfully!');
        
        if (isGlobal) {
          await fetchGlobalRules();
        } else {
          await fetchDocumentRules();
        }
        
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        throw new Error(response.data?.error || 'Failed to delete rule');
      }
    } catch (error) {
      console.error('Error deleting rule:', error);
      setError('Failed to delete rule. Please try again.');
    }
  };

  const clearError = () => setError('');

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Enhanced Rule Management
        </h2>
        <p className="text-gray-600">
          Manage global compliance rules and document-specific requirements for comprehensive analysis.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setActiveTab('global')}
          className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'global'
              ? 'border-blue-500 text-blue-600 bg-blue-50'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Global Rules
          </div>
        </button>
        {documentId && (
          <button
            onClick={() => setActiveTab('document')}
            className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'document'
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Document-Specific Rules
            </div>
          </button>
        )}
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <p className="text-green-700 text-sm">{successMessage}</p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-red-700 text-sm">{error}</p>
              <button 
                onClick={clearError}
                className="text-red-600 text-sm underline mt-1 hover:text-red-800"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rule Input Form */}
      <div className="mb-8 p-6 bg-gray-50 rounded-lg">
        <label className="block text-sm font-medium text-gray-700 mb-4">
          New {activeTab === 'global' ? 'Global' : 'Document-Specific'} Rule
        </label>
        
        <div className="flex gap-4 mb-4">
          <div className="w-32">
            <label className="block text-xs font-medium text-gray-600 mb-1">Severity</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="Critical">Critical</option>
              <option value="Major">Major</option>
              <option value="Minor">Minor</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-600 mb-1">Rule Type</label>
            <input
              type="text"
              value="Custom"
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 text-sm"
            />
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 mb-1">Rule Description</label>
          <textarea
            value={newRuleText}
            onChange={(e) => setNewRuleText(e.target.value)}
            placeholder={`Example: ${activeTab === 'global' 
              ? 'All documents must include a valid electronic signature section with clear procedures for user authentication and audit trail requirements...'
              : 'This document must contain specific validation procedures for data integrity and backup protocols according to company policy...'
            }`}
            className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-sm"
            disabled={isSaving}
          />
          <p className="text-xs text-gray-500 mt-1">
            Describe the compliance requirement in plain English. 
            {activeTab === 'global' 
              ? ' This rule will apply to all future document analyses.'
              : ' This rule will only apply to this specific document.'
            }
          </p>
        </div>

        <button
          onClick={handleSaveRule}
          disabled={isSaving || !newRuleText.trim() || (activeTab === 'document' && !documentId)}
          className={`inline-flex items-center px-4 py-2 rounded-lg font-medium text-white transition-colors duration-200 ${
            isSaving || !newRuleText.trim() || (activeTab === 'document' && !documentId)
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:ring-blue-200'
          }`}
        >
          {isSaving ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Saving...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Save {activeTab === 'global' ? 'Global' : 'Document'} Rule
            </>
          )}
        </button>
      </div>

      {/* Rules List */}
      <div className="space-y-6">
        {activeTab === 'global' ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Global Rules ({globalRules.length})
              </h3>
              <button
                onClick={fetchGlobalRules}
                disabled={isLoading}
                className="text-sm text-blue-600 hover:text-blue-800 underline"
              >
                {isLoading ? 'Loading...' : 'Refresh'}
              </button>
            </div>
            
            {globalRules.length > 0 ? (
              <div className="space-y-3">
                {globalRules.map((rule, index) => (
                  <div key={rule.id || index} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            rule.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                            rule.severity === 'Major' ? 'bg-orange-100 text-orange-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {rule.severity}
                          </span>
                          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                            {rule.rule_type || 'Custom'}
                          </span>
                        </div>
                        <p className="text-gray-700 text-sm leading-relaxed">
                          {rule.rule_text}
                        </p>
                        {rule.created_at && (
                          <p className="text-xs text-gray-400 mt-2">
                            Added: {new Date(rule.created_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      {rule.id && (
                        <button
                          onClick={() => handleDeleteRule(rule.id, true)}
                          className="ml-4 text-red-600 hover:text-red-800 p-1 hover:bg-red-50 rounded"
                          title="Delete rule"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-gray-500 mb-2">No global rules found</p>
                <p className="text-gray-400 text-sm">Add your first global compliance rule above</p>
              </div>
            )}
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Document-Specific Rules ({documentRules.length})
              </h3>
              <button
                onClick={fetchDocumentRules}
                disabled={!documentId}
                className="text-sm text-blue-600 hover:text-blue-800 underline"
              >
                Refresh
              </button>
            </div>
            
            {!documentId ? (
              <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-gray-500 mb-2">No document selected</p>
                <p className="text-gray-400 text-sm">Document-specific rules require a document context</p>
              </div>
            ) : documentRules.length > 0 ? (
              <div className="space-y-3">
                {documentRules.map((rule, index) => (
                  <div key={rule.id || index} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            rule.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                            rule.severity === 'Major' ? 'bg-orange-100 text-orange-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {rule.severity}
                          </span>
                          <span className="text-xs text-gray-500 bg-blue-100 px-2 py-1 rounded">
                            Document-Specific
                          </span>
                        </div>
                        <p className="text-gray-700 text-sm leading-relaxed">
                          {rule.rule_text}
                        </p>
                        {rule.created_at && (
                          <p className="text-xs text-gray-400 mt-2">
                            Added: {new Date(rule.created_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      {rule.id && (
                        <button
                          onClick={() => handleDeleteRule(rule.id, false)}
                          className="ml-4 text-red-600 hover:text-red-800 p-1 hover:bg-red-50 rounded"
                          title="Delete rule"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-gray-500 mb-2">No document-specific rules found</p>
                <p className="text-gray-400 text-sm">Add your first document-specific rule above</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedRuleEditor;