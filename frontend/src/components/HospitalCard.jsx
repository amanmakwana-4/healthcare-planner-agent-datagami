import React from 'react';
import { Building2, MapPin, Clock, Stethoscope } from 'lucide-react';

const HospitalCard = ({ hospital, index }) => {
  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow duration-200 animate-fadeIn"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4 flex-1">
          <div className="bg-blue-100 dark:bg-blue-900 rounded-lg p-3 shrink-0">
            <Building2 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-white text-base mb-1">
              {hospital.name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-1">
              <MapPin className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{hospital.location || 'Location not available'}</span>
            </p>

            <p className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-1 mt-2">
              <Clock className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{hospital.timing || 'Timing not available'}</span>
            </p>

            {hospital.specialistDoctors && hospital.specialistDoctors.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 uppercase tracking-wide flex items-center gap-1">
                  <Stethoscope className="w-3 h-3" />
                  Specialist Doctors
                </p>
                <ul className="space-y-1">
                  {hospital.specialistDoctors.slice(0, 2).map((doc, i) => (
                    <li key={i} className="text-xs text-gray-700 dark:text-gray-300">
                      {doc}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HospitalCard;
