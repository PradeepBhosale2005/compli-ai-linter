/**
 * RuleEditor Component
 * 
 * A React component that allows users to add new, dynamic GxP rules.
 * Provides a UI for adding new compliance rules in plain English and managing existing rules.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RuleEditor = () => {
  // Component state
  const [newRuleText, setNewRuleText] = useState('');
  const [savedRules, setSavedRules] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [error, setError] = useState('');

  // Fetch existing rules on component mount
  useEffect(() => {
    fetchRules();
  }, []);

  // Fetch existing rules from backend
  const fetchRules = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const response = await axios.get('http://localhost:8000/get-rules/');
      
      if (response.data && response.data.success) {
        setSavedRules(response.data.rules || []);
      } else {
        console.warn('No rules found or unexpected response format');
        setSavedRules([]);
      }
    } catch (error) {
      console.error('Error fetching rules:', error);
      if (error.response?.status === 404) {
        // Endpoint might not exist yet - this is expected
        setSavedRules([]);
      } else {
        setError('Failed to load existing rules. You can still add new rules.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Save new rule to backend
  const handleSaveRule = async () => {
    if (!newRuleText.trim()) {
      setError('Please enter a rule description before saving.');
      return;
    }

    try {
      setIsSaving(true);
      setError('');
      setSuccessMessage('');

      const response = await axios.post(
        'http://localhost:8000/add-rule/',
        {
          rule_text: newRuleText.trim(),
          rule_type: 'Custom',
          severity: 'Major' // Default severity, could be made configurable
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 30000,
        }
      );

      if (response.data && response.data.success) {
        // Success - clear form and show success message
        setNewRuleText('');
        setSuccessMessage('Rule saved successfully!');
        
        // Refresh the rules list
        await fetchRules();
        
        // Clear success message after 3 seconds
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        throw new Error(response.data?.error || 'Failed to save rule');
      }
    } catch (error) {
      console.error('Error saving rule:', error);
      
      let errorMessage = 'Failed to save rule. Please try again.';
      if (error.response) {
        errorMessage = error.response.data?.detail || error.response.data?.error || errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  // Delete a rule
  const handleDeleteRule = async (ruleId) => {
    if (!window.confirm('Are you sure you want to delete this rule?')) {
      return;
    }

    try {
      const response = await axios.delete(`http://localhost:8000/delete-rule/${ruleId}`);
      
      if (response.data && response.data.success) {
        setSuccessMessage('Rule deleted successfully!');
        await fetchRules();
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        throw new Error(response.data?.error || 'Failed to delete rule');
      }
    } catch (error) {
      console.error('Error deleting rule:', error);
      setError('Failed to delete rule. Please try again.');
    }
  };

  // Clear error messages
  const clearError = () => setError('');

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Dynamic Rule Editor
        </h2>
        <p className="text-gray-600">
          Add custom compliance rules in plain English. These rules will be automatically applied to future document analyses.
        </p>
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
      <div className="mb-8">
        <label htmlFor="rule-text" className="block text-sm font-medium text-gray-700 mb-2">
          New Compliance Rule
        </label>
        <textarea
          id="rule-text"
          value={newRuleText}
          onChange={(e) => setNewRuleText(e.target.value)}
          placeholder="Example: All documents must include a valid electronic signature section with clear procedures for user authentication and audit trail requirements..."
          className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          disabled={isSaving}
        />
        <p className="text-xs text-gray-500 mt-1">
          Describe the compliance requirement in plain English. The system will automatically apply this rule to future analyses.
        </p>
        
        <button
          onClick={handleSaveRule}
          disabled={isSaving || !newRuleText.trim()}
          className={`mt-4 inline-flex items-center px-4 py-2 rounded-lg font-medium text-white transition-colors duration-200 ${
            isSaving || !newRuleText.trim()
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
              Saving Rule...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Save Rule
            </>
          )}
        </button>
      </div>

      {/* Existing Rules List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Existing Rules ({savedRules.length})
          </h3>
          <button
            onClick={fetchRules}
            disabled={isLoading}
            className="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <svg className="animate-spin h-8 w-8 text-gray-400 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-gray-500 mt-2">Loading rules...</p>
          </div>
        ) : savedRules.length > 0 ? (
          <div className="space-y-3">
            {savedRules.map((rule, index) => (
              <div key={rule.id || index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        rule.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                        rule.severity === 'Major' ? 'bg-orange-100 text-orange-800' :
                        rule.severity === 'Minor' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {rule.severity || 'Major'}
                      </span>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {rule.rule_type || 'Custom'}
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm leading-relaxed">
                      {rule.rule_text || rule.description || 'No description available'}
                    </p>
                    {rule.created_at && (
                      <p className="text-xs text-gray-400 mt-2">
                        Added: {new Date(rule.created_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  {rule.id && (
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      className="ml-4 text-red-600 hover:text-red-800 p-1"
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
            <p className="text-gray-500 mb-2">No custom rules found</p>
            <p className="text-gray-400 text-sm">Add your first custom compliance rule above</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default RuleEditor;