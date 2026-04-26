import React from 'react';
import { User, Briefcase, Clock, Building2 } from 'lucide-react';

const DoctorCard = ({ doctor, index }) => {
  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow duration-200 animate-fadeIn"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start gap-4">
        <div className="bg-teal-100 dark:bg-teal-900 rounded-lg p-3 flex-shrink-0">
          <User className="w-6 h-6 text-teal-600 dark:text-teal-400" />
        </div>
        <div className="flex-1 min-w-0">
          {/* Name */}
          <h3 className="font-semibold text-gray-900 dark:text-white text-base mb-2">
            {doctor.name}
          </h3>

          {/* Specialization */}
          {doctor.specialization && (
            <div className="flex items-center gap-2 mb-2">
              <Briefcase className="w-4 h-4 text-gray-500 dark:text-gray-400 flex-shrink-0" />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {doctor.specialization}
              </span>
            </div>
          )}

          {/* Timing */}
          {doctor.timing && (
            <div className="inline-flex items-center gap-2 bg-teal-50 dark:bg-teal-900/30 px-3 py-1 rounded-lg mb-2">
              <Clock className="w-4 h-4 text-teal-600 dark:text-teal-400 flex-shrink-0" />
              <span className="text-xs font-medium text-teal-700 dark:text-teal-300">
                {doctor.timing}
              </span>
            </div>
          )}

          {/* Hospital */}
          {doctor.hospital && (
            <div className="flex items-start gap-2 mt-2">
              <Building2 className="w-4 h-4 text-gray-500 dark:text-gray-400 flex-shrink-0 mt-0.5" />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {doctor.hospital}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DoctorCard;
