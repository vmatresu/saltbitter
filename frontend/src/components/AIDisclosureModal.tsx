import React from 'react';

interface AIDisclosureModalProps {
  isOpen: boolean;
  onAccept: () => void;
  onDecline: () => void;
}

export const AIDisclosureModal: React.FC<AIDisclosureModalProps> = ({
  isOpen,
  onAccept,
  onDecline,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center gap-3 mb-4">
          <div className="text-4xl">🤖</div>
          <h2 className="text-2xl font-bold text-gray-900">AI Feature Disclosure</h2>
        </div>

        <div className="space-y-4 text-gray-700">
          <p>
            This feature uses artificial intelligence (AI) to provide practice conversations
            and relationship coaching.
          </p>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 className="font-semibold text-purple-900 mb-2">🇪🇺 EU AI Act Compliance</h3>
            <p className="text-sm text-purple-800">
              All AI-generated content is clearly labeled with a 🤖 badge in compliance with
              EU AI Act Article 52 transparency requirements.
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">📋 California SB 243 Compliance</h3>
            <p className="text-sm text-blue-800">
              You have the right to opt out of AI features at any time through your settings.
              Human alternatives are available for all AI features.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">What we use AI for:</h3>
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li>Practice conversation partners with different personalities</li>
              <li>Personalized relationship coaching and communication tips</li>
              <li>Conversation analysis and feedback</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Your data and privacy:</h3>
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li>All AI interactions are logged for compliance and quality</li>
              <li>Your data is not shared with third parties</li>
              <li>You can request deletion of your data at any time</li>
              <li>AI companions never impersonate real people</li>
            </ul>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-700">
              <strong>Important:</strong> AI companions are designed for practice and
              should not replace real human connections or professional therapy. If you
              need mental health support, please consult a licensed professional.
            </p>
          </div>
        </div>

        <div className="flex gap-4 mt-6">
          <button onClick={onDecline} className="btn-outline flex-1">
            Decline
          </button>
          <button onClick={onAccept} className="btn-primary flex-1">
            Accept & Continue
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center mt-4">
          You can change your AI preferences at any time in Settings
        </p>
      </div>
    </div>
  );
};

export default AIDisclosureModal;
