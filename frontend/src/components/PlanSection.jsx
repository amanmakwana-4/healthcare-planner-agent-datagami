import React from 'react';
import { ClipboardList } from 'lucide-react';

const PlanSection = ({ plan }) => {
  if (!plan) return null;

  // Split plan by lines and filter empty ones
  const lines = plan.split('\n').filter((line) => line.trim());

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 md:p-8 shadow-sm border border-gray-200 dark:border-gray-700 animate-fadeIn">
      <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
        <ClipboardList className="w-7 h-7 text-blue-600 dark:text-blue-400" />
        Your Healthcare Plan
      </h2>

      <div className="space-y-3">
        {lines.map((line, index) => {
          const isHeading = line.startsWith('##') || /^[A-Z][^]*:$/.test(line);
          const cleanLine = line.replace(/^#+\s*/, '');

          if (isHeading) {
            return (
              <h3
                key={index}
                className="text-lg md:text-xl font-semibold text-gray-900 dark:text-white mt-4 pt-2 border-t border-gray-200 dark:border-gray-700"
              >
                {cleanLine}
              </h3>
            );
          }

          const isBullet = line.trim().startsWith('-') || line.trim().startsWith('•');
          if (isBullet) {
            return (
              <div key={index} className="flex items-start gap-3 ml-2">
                <span className="inline-block w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  {cleanLine.replace(/^[-•]\s*/, '')}
                </p>
              </div>
            );
          }

          return (
            <p
              key={index}
              className="text-gray-700 dark:text-gray-300 leading-relaxed"
            >
              {cleanLine}
            </p>
          );
        })}
      </div>
    </div>
  );
};

export default PlanSection;
