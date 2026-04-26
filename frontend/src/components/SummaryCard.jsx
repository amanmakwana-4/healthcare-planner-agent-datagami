import React from 'react';
import { Heart, Activity, Pill } from 'lucide-react';

const SummaryCard = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="bg-gradient-to-br from-blue-50 to-teal-50 dark:from-gray-800 dark:to-gray-800 rounded-2xl p-6 md:p-8 shadow-sm border border-blue-100 dark:border-gray-700 animate-fadeIn">
      {/* Title */}
      <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
        <Heart className="w-7 h-7 text-red-500" />
        Condition Overview
      </h2>

      {/* Description */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-2">
          Description
        </h3>
        <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
          {summary.description}
        </p>
      </div>

      {/* Symptoms */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Symptoms
        </h3>
        <ul className="space-y-2">
          {summary.symptoms && summary.symptoms.length > 0 ? (
            summary.symptoms.map((symptom, i) => (
              <li
                key={i}
                className="flex items-start gap-3 text-gray-800 dark:text-gray-200"
              >
                <span className="inline-block w-2 h-2 bg-teal-500 rounded-full mt-2 flex-shrink-0" />
                <span>{symptom}</span>
              </li>
            ))
          ) : (
            <p className="text-gray-600 dark:text-gray-400">No symptoms provided</p>
          )}
        </ul>
      </div>

      {/* Treatments */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
          <Pill className="w-4 h-4" />
          Treatment Guidance
        </h3>
        <ul className="space-y-2">
          {summary.treatments && summary.treatments.length > 0 ? (
            summary.treatments.map((treatment, i) => (
              <li
                key={i}
                className="flex items-start gap-3 text-gray-800 dark:text-gray-200"
              >
                <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                <span>{treatment}</span>
              </li>
            ))
          ) : (
            <p className="text-gray-600 dark:text-gray-400">No treatments provided</p>
          )}
        </ul>
      </div>

      {/* Specialist */}
      <div className="bg-white dark:bg-gray-700 rounded-xl p-4 border-l-4 border-teal-500">
        <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-2">
          Recommended Specialist
        </p>
        <p className="text-lg md:text-xl font-semibold text-teal-600 dark:text-teal-400">
          {summary.specialist || 'General Practitioner'}
        </p>
      </div>
    </div>
  );
};

export default SummaryCard;
