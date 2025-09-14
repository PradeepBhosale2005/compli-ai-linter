/**
 * ScoreCard Component
 * 
 * A React component to display the overall compliance score in a large, circular format.
 * It accepts a `score` number as a prop and displays it prominently with dynamic colors
 * based on the score value using Tailwind CSS classes.
 */

import React from 'react';

const ScoreCard = ({ score = 0, maxScore = 100, label = "Compliance Score" }) => {
  // Define score-based styling
  const getScoreStyles = (scoreValue) => {
    if (scoreValue >= 90) {
      return {
        circleColor: 'bg-green-100 border-green-300',
        textColor: 'text-green-700',
        ringColor: 'ring-green-200',
        gradientFrom: 'from-green-50',
        gradientTo: 'to-green-100'
      };
    } else if (scoreValue >= 70) {
      return {
        circleColor: 'bg-blue-100 border-blue-300',
        textColor: 'text-blue-700',
        ringColor: 'ring-blue-200',
        gradientFrom: 'from-blue-50',
        gradientTo: 'to-blue-100'
      };
    } else if (scoreValue >= 50) {
      return {
        circleColor: 'bg-yellow-100 border-yellow-300',
        textColor: 'text-yellow-700',
        ringColor: 'ring-yellow-200',
        gradientFrom: 'from-yellow-50',
        gradientTo: 'to-yellow-100'
      };
    } else if (scoreValue >= 30) {
      return {
        circleColor: 'bg-orange-100 border-orange-300',
        textColor: 'text-orange-700',
        ringColor: 'ring-orange-200',
        gradientFrom: 'from-orange-50',
        gradientTo: 'to-orange-100'
      };
    } else {
      return {
        circleColor: 'bg-red-100 border-red-300',
        textColor: 'text-red-700',
        ringColor: 'ring-red-200',
        gradientFrom: 'from-red-50',
        gradientTo: 'to-red-100'
      };
    }
  };

  // Get compliance level text
  const getComplianceLevel = (scoreValue) => {
    if (scoreValue >= 90) return 'Excellent';
    if (scoreValue >= 70) return 'Good';
    if (scoreValue >= 50) return 'Fair';
    if (scoreValue >= 30) return 'Poor';
    return 'Critical';
  };

  const styles = getScoreStyles(score);
  const complianceLevel = getComplianceLevel(score);
  
  // Calculate percentage for progress indicator
  const percentage = Math.min(Math.max(score / maxScore * 100, 0), 100);

  return (
    <div className="flex flex-col items-center p-8">
      {/* Main circular score display */}
      <div className="relative">
        {/* Background circle with gradient */}
        <div className={`w-48 h-48 rounded-full ${styles.circleColor} border-4 ${styles.circleColor.replace('bg-', 'border-')} shadow-lg bg-gradient-to-br ${styles.gradientFrom} ${styles.gradientTo} flex items-center justify-center relative overflow-hidden`}>
          
          {/* Progress ring overlay */}
          <div className="absolute inset-0 rounded-full">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              {/* Background ring */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-white/30"
              />
              {/* Progress ring */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray={`${percentage * 2.827} 282.7`}
                className={styles.textColor}
                style={{
                  transition: 'stroke-dasharray 1s ease-in-out'
                }}
              />
            </svg>
          </div>

          {/* Score content */}
          <div className="text-center z-10">
            <div className={`text-5xl font-bold ${styles.textColor} leading-none`}>
              {Math.round(score)}
            </div>
            <div className={`text-lg font-medium ${styles.textColor} opacity-80`}>
              / {maxScore}
            </div>
          </div>
        </div>

        {/* Floating percentage indicator */}
        <div className={`absolute -top-2 -right-2 ${styles.circleColor} ${styles.textColor} text-xs font-semibold px-3 py-1 rounded-full border-2 border-white shadow-md`}>
          {Math.round(percentage)}%
        </div>
      </div>

      {/* Score label and compliance level */}
      <div className="text-center mt-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-1">
          {label}
        </h3>
        <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${styles.circleColor} ${styles.textColor} border ${styles.circleColor.replace('bg-', 'border-')}`}>
          {complianceLevel}
        </div>
      </div>

      {/* Additional score context */}
      <div className="text-center mt-4 text-gray-600">
        <p className="text-sm">
          {score >= 90 && "Outstanding compliance standards"}
          {score >= 70 && score < 90 && "Meets most compliance requirements"}
          {score >= 50 && score < 70 && "Partial compliance achieved"}
          {score >= 30 && score < 50 && "Significant improvements needed"}
          {score < 30 && "Critical compliance issues detected"}
        </p>
      </div>
    </div>
  );
};

export default ScoreCard;