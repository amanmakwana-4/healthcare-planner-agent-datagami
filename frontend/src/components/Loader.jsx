import React from 'react';

const SkeletonLoader = ({ count = 1, type = 'card' }) => {
  if (type === 'card') {
    return (
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="bg-gray-200 dark:bg-gray-700 rounded-lg h-20 animate-pulse" />
        ))}
      </div>
    );
  }

  if (type === 'text') {
    return (
      <div className="space-y-2">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="bg-gray-200 dark:bg-gray-700 rounded h-4 animate-pulse w-full" />
        ))}
      </div>
    );
  }

  if (type === 'summary') {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="bg-gray-200 dark:bg-gray-700 rounded h-6 w-40 animate-pulse" />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i}>
              <div className="bg-gray-200 dark:bg-gray-700 rounded h-4 w-24 animate-pulse mb-2" />
              <div className="space-y-2">
                <div className="bg-gray-200 dark:bg-gray-700 rounded h-3 w-full animate-pulse" />
                <div className="bg-gray-200 dark:bg-gray-700 rounded h-3 w-5/6 animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
};

export default SkeletonLoader;
