import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Settings, 
  Moon, 
  Sun, 
  Monitor,
  Zap,
  Database,
  Keyboard,
  Bell,
  Save
} from 'lucide-react';
import { cn } from '../utils/cn';

function SettingsPanel({ settings, onSettingsChange, isBackendReady }) {
  const [localSettings, setLocalSettings] = useState(settings);
  const [hasChanges, setHasChanges] = useState(false);

  const updateSetting = (key, value) => {
    const newSettings = { ...localSettings, [key]: value };
    setLocalSettings(newSettings);
    setHasChanges(true);
  };

  const saveSettings = () => {
    onSettingsChange(localSettings);
    setHasChanges(false);
  };

  const resetSettings = () => {
    setLocalSettings(settings);
    setHasChanges(false);
  };

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Settings className="w-6 h-6" />
          Settings
        </h2>
        <p className="text-muted-foreground">
          Configure your semantic search assistant
        </p>
      </div>

      {/* Settings Content */}
      <div className="flex-1 overflow-y-auto space-y-6">
        
        {/* Appearance */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Monitor className="w-5 h-5" />
            Appearance
          </h3>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-2">Theme</label>
              <div className="flex gap-2">
                {[
                  { value: 'light', label: 'Light', icon: Sun },
                  { value: 'dark', label: 'Dark', icon: Moon },
                  { value: 'system', label: 'System', icon: Monitor }
                ].map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => updateSetting('theme', value)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-md border transition-colors",
                      localSettings.theme === value
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-border hover:bg-muted"
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Search Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Database className="w-5 h-5" />
            Search & Processing
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Chunk Size
              </label>
              <input
                type="range"
                min="500"
                max="2000"
                step="100"
                value={localSettings.chunkSize}
                onChange={(e) => updateSetting('chunkSize', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>500</span>
                <span>{localSettings.chunkSize} characters</span>
                <span>2000</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Chunk Overlap
              </label>
              <input
                type="range"
                min="50"
                max="500"
                step="50"
                value={localSettings.chunkOverlap}
                onChange={(e) => updateSetting('chunkOverlap', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>50</span>
                <span>{localSettings.chunkOverlap} characters</span>
                <span>500</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Auto-index new files</label>
                <p className="text-xs text-muted-foreground">
                  Automatically process files when added to watched folders
                </p>
              </div>
              <input
                type="checkbox"
                checked={localSettings.autoIndex}
                onChange={(e) => updateSetting('autoIndex', e.target.checked)}
                className="rounded"
              />
            </div>
          </div>
        </div>

        {/* Floating Window */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Floating Window
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Always on top</label>
                <p className="text-xs text-muted-foreground">
                  Keep floating window above other applications
                </p>
              </div>
              <input
                type="checkbox"
                checked={localSettings.alwaysOnTop}
                onChange={(e) => updateSetting('alwaysOnTop', e.target.checked)}
                className="rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Auto-hide when inactive</label>
                <p className="text-xs text-muted-foreground">
                  Hide floating window when not in use
                </p>
              </div>
              <input
                type="checkbox"
                checked={localSettings.autoHide}
                onChange={(e) => updateSetting('autoHide', e.target.checked)}
                className="rounded"
              />
            </div>
          </div>
        </div>

        {/* Keyboard Shortcuts */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Keyboard className="w-5 h-5" />
            Keyboard Shortcuts
          </h3>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border border-border rounded-lg">
              <div>
                <div className="text-sm font-medium">Toggle Floating Window</div>
                <div className="text-xs text-muted-foreground">Show/hide the floating search window</div>
              </div>
              <kbd className="px-2 py-1 bg-muted rounded text-xs">Ctrl+Shift+Space</kbd>
            </div>
            
            <div className="flex items-center justify-between p-3 border border-border rounded-lg">
              <div>
                <div className="text-sm font-medium">Focus Search</div>
                <div className="text-xs text-muted-foreground">Focus the search input</div>
              </div>
              <kbd className="px-2 py-1 bg-muted rounded text-xs">Ctrl+K</kbd>
            </div>
            
            <div className="flex items-center justify-between p-3 border border-border rounded-lg">
              <div>
                <div className="text-sm font-medium">Quick Search</div>
                <div className="text-xs text-muted-foreground">Global search shortcut</div>
              </div>
              <kbd className="px-2 py-1 bg-muted rounded text-xs">Ctrl+Alt+F</kbd>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notifications
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Processing notifications</label>
                <p className="text-xs text-muted-foreground">
                  Show notifications when documents are processed
                </p>
              </div>
              <input
                type="checkbox"
                checked={localSettings.showNotifications}
                onChange={(e) => updateSetting('showNotifications', e.target.checked)}
                className="rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium">Error notifications</label>
                <p className="text-xs text-muted-foreground">
                  Show notifications for errors and failures
                </p>
              </div>
              <input
                type="checkbox"
                checked={localSettings.showErrors}
                onChange={(e) => updateSetting('showErrors', e.target.checked)}
                className="rounded"
              />
            </div>
          </div>
        </div>

        {/* Backend Status */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Backend Status</h3>
          
          <div className="p-4 border border-border rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <div className={cn(
                "w-3 h-3 rounded-full",
                isBackendReady ? "bg-green-500" : "bg-yellow-500 animate-pulse"
              )} />
              <span className="font-medium">
                {isBackendReady ? 'Connected' : 'Starting...'}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {isBackendReady 
                ? 'Backend is running and ready to process requests'
                : 'Backend is starting up, please wait...'
              }
            </p>
          </div>
        </div>
      </div>

      {/* Save/Reset Buttons */}
      {hasChanges && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex gap-2 pt-4 border-t border-border"
        >
          <button
            onClick={saveSettings}
            className="btn btn-primary flex-1"
          >
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </button>
          <button
            onClick={resetSettings}
            className="btn btn-secondary"
          >
            Reset
          </button>
        </motion.div>
      )}
    </div>
  );
}

export default SettingsPanel;
