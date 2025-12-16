'use client';

import { useState, useEffect } from 'react';
import { X, Rocket, Check, Save } from 'lucide-react';
import { cn } from '@/lib/utils';
import { promptsAPI } from '@/lib/api';
import type { GroupedPromptTab, SetupProfile } from '@/types';

interface QuickSetupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: (promptIds: number[], additionalText?: string) => void;
}

export default function QuickSetupModal({ isOpen, onClose, onApply }: QuickSetupModalProps) {
  const [promptTabs, setPromptTabs] = useState<GroupedPromptTab[]>([]);
  const [profiles, setProfiles] = useState<SetupProfile[]>([]);
  const [selectedPrompts, setSelectedPrompts] = useState<Set<number>>(new Set());
  const [additionalText, setAdditionalText] = useState('');
  const [loading, setLoading] = useState(false);
  const [saveProfileName, setSaveProfileName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    try {
      const [tabs, profilesData] = await Promise.all([
        promptsAPI.getGroupedTemplates(),
        promptsAPI.getProfiles(),
      ]);
      setPromptTabs(tabs);
      setProfiles(profilesData);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const togglePrompt = (promptId: number) => {
    setSelectedPrompts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(promptId)) {
        newSet.delete(promptId);
      } else {
        newSet.add(promptId);
      }
      return newSet;
    });
  };

  const selectAll = () => {
    const allIds = new Set<number>();
    promptTabs.forEach((tab) => {
      tab.subtabs.forEach((subtab) => {
        allIds.add(subtab.id);
      });
    });
    setSelectedPrompts(allIds);
  };

  const deselectAll = () => {
    setSelectedPrompts(new Set());
  };

  const applyProfile = (profile: SetupProfile) => {
    setSelectedPrompts(new Set(profile.prompt_ids));
  };

  const handleSaveProfile = async () => {
    if (!saveProfileName.trim() || selectedPrompts.size === 0) return;

    try {
      await promptsAPI.createProfile(saveProfileName.trim(), Array.from(selectedPrompts));
      await loadData();
      setSaveProfileName('');
      setShowSaveDialog(false);
    } catch (error) {
      console.error('Failed to save profile:', error);
    }
  };

  const handleApply = () => {
    if (selectedPrompts.size === 0) return;
    setLoading(true);
    onApply(Array.from(selectedPrompts), additionalText || undefined);
    setLoading(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-900 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden shadow-2xl border border-dark-700">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-700">
          <div className="flex items-center gap-2">
            <Rocket className="w-5 h-5 text-accent-blue" />
            <h2 className="text-lg font-semibold text-dark-100">Quick Setup</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-dark-400" />
          </button>
        </div>

        {/* Profiles */}
        {profiles.length > 0 && (
          <div className="p-4 border-b border-dark-700">
            <h3 className="text-sm font-medium text-dark-300 mb-2">Saved Profiles</h3>
            <div className="flex flex-wrap gap-2">
              {profiles.map((profile) => (
                <button
                  key={profile.id}
                  onClick={() => applyProfile(profile)}
                  className="px-3 py-1.5 bg-dark-800 hover:bg-dark-700 text-dark-200 text-sm rounded-lg transition-colors"
                >
                  ▶ {profile.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Prompt Selection */}
        <div className="p-4 overflow-y-auto max-h-[40vh]">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-dark-300">Select Prompts</h3>
            <div className="flex gap-2">
              <button
                onClick={selectAll}
                className="text-xs text-accent-blue hover:underline"
              >
                Select All
              </button>
              <button
                onClick={deselectAll}
                className="text-xs text-dark-400 hover:underline"
              >
                Deselect All
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {promptTabs.map((tab) => (
              <div key={tab.tab_name}>
                <h4 className="text-sm font-medium text-dark-200 mb-2">📁 {tab.tab_name}</h4>
                <div className="grid grid-cols-2 gap-2 ml-4">
                  {tab.subtabs.map((subtab) => (
                    <button
                      key={subtab.id}
                      onClick={() => togglePrompt(subtab.id)}
                      className={cn(
                        "flex items-center gap-2 p-2 text-left text-sm rounded-lg transition-colors",
                        selectedPrompts.has(subtab.id)
                          ? "bg-accent-blue/20 text-accent-blue border border-accent-blue/30"
                          : "bg-dark-800 text-dark-300 hover:bg-dark-700"
                      )}
                    >
                      <div className={cn(
                        "w-4 h-4 rounded border flex items-center justify-center flex-shrink-0",
                        selectedPrompts.has(subtab.id)
                          ? "bg-accent-blue border-accent-blue"
                          : "border-dark-600"
                      )}>
                        {selectedPrompts.has(subtab.id) && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </div>
                      <span className="truncate">{subtab.subtab_name}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Additional Text */}
        <div className="p-4 border-t border-dark-700">
          <label className="text-sm font-medium text-dark-300 mb-2 block">
            Additional Instructions (Optional)
          </label>
          <textarea
            value={additionalText}
            onChange={(e) => setAdditionalText(e.target.value)}
            placeholder="Add any extra context or instructions..."
            className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-dark-200 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-accent-blue"
            rows={2}
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-dark-700 bg-dark-800">
          <div className="flex items-center gap-2">
            <span className="text-sm text-dark-400">
              {selectedPrompts.size} prompts selected
            </span>
            {!showSaveDialog ? (
              <button
                onClick={() => setShowSaveDialog(true)}
                className="flex items-center gap-1 text-sm text-accent-blue hover:underline"
                disabled={selectedPrompts.size === 0}
              >
                <Save className="w-3.5 h-3.5" />
                Save Profile
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={saveProfileName}
                  onChange={(e) => setSaveProfileName(e.target.value)}
                  placeholder="Profile name..."
                  className="px-2 py-1 bg-dark-900 border border-dark-600 rounded text-sm text-dark-200 focus:outline-none focus:ring-1 focus:ring-accent-blue"
                  autoFocus
                />
                <button
                  onClick={handleSaveProfile}
                  disabled={!saveProfileName.trim()}
                  className="text-sm text-accent-green hover:underline"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setShowSaveDialog(false);
                    setSaveProfileName('');
                  }}
                  className="text-sm text-dark-400 hover:underline"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-dark-300 hover:bg-dark-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              disabled={selectedPrompts.size === 0 || loading}
              className={cn(
                "flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors",
                selectedPrompts.size > 0 && !loading
                  ? "bg-accent-blue hover:bg-accent-blue/90 text-white"
                  : "bg-dark-700 text-dark-500 cursor-not-allowed"
              )}
            >
              <Rocket className="w-4 h-4" />
              Apply {selectedPrompts.size > 0 && `(${selectedPrompts.size})`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}




