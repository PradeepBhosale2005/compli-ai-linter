/**
 * FindingCard Component
 * 
 * A React component to display a single compliance finding in a card format.
 * It accepts a `finding` object as a prop, which includes severity, description, and explanation.
 * The card's left border color dynamically changes based on the severity using Tailwind CSS classes.
 */

import React from 'react';

const FindingCard = ({ finding }) => {
  // Define severity-based styling
  const getSeverityStyles = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return {
          borderColor: 'border-l-red-500',
          badgeColor: 'bg-red-100 text-red-800',
          iconColor: 'text-red-500'
        };
      case 'major':
        return {
          borderColor: 'border-l-orange-500',
          badgeColor: 'bg-orange-100 text-orange-800',
          iconColor: 'text-orange-500'
        };
      case 'minor':
        return {
          borderColor: 'border-l-yellow-500',
          badgeColor: 'bg-yellow-100 text-yellow-800',
          iconColor: 'text-yellow-500'
        };
      default:
        return {
          borderColor: 'border-l-gray-500',
          badgeColor: 'bg-gray-100 text-gray-800',
          iconColor: 'text-gray-500'
        };
    }
  };

  const styles = getSeverityStyles(finding?.severity);

  return (
    <div className={`bg-white rounded-lg shadow-md border-l-4 ${styles.borderColor} p-6 mb-4 hover:shadow-lg transition-shadow duration-200`}>
      {/* Header with severity badge */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Severity indicator icon */}
          <div className={`w-3 h-3 rounded-full ${styles.iconColor.replace('text-', 'bg-')}`}></div>
          
          {/* Severity badge */}
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${styles.badgeColor}`}>
            {finding?.severity || 'Unknown'}
          </span>
        </div>

        {/* Rule type indicator */}
        {finding?.rule_type && (
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {finding.rule_type}
          </span>
        )}
      </div>

      {/* Finding description */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {finding?.title || 'Compliance Issue'}
        </h3>
        <p className="text-gray-700 leading-relaxed">
          {finding?.description || 'No description available'}
        </p>
      </div>

      {/* Detailed explanation */}
      {finding?.explanation && (
        <div className="border-t border-gray-200 pt-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            Explanation
          </h4>
          <p className="text-sm text-gray-600 leading-relaxed">
            {finding.explanation}
          </p>
        </div>
      )}

      {/* Additional metadata */}
      {(finding?.section || finding?.line_number) && (
        <div className="border-t border-gray-200 pt-3 mt-4">
          <div className="flex flex-wrap gap-4 text-xs text-gray-500">
            {finding.section && (
              <span>
                <strong>Section:</strong> {finding.section}
              </span>
            )}
            {finding.line_number && (
              <span>
                <strong>Line:</strong> {finding.line_number}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FindingCard;