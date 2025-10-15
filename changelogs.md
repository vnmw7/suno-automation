# Suno Automation Changelogs

## 2025-10-15

### Fixed and Enhanced Docker Pull Scripts
- **Fixed**: Resolved immediate closing issue in `pull-images.bat` caused by parentheses syntax error
- **Added**: Extensive debug output and logging in both Windows and Linux scripts
- **Features**:
  - Console window title "Suno Docker Pull Images" for visibility
  - Docker availability and daemon status checks
  - Step-by-step action logging with timestamps
  - Clear error messages with common troubleshooting tips
  - Visual separators and progress indicators
- **Changed**: Replaced problematic parentheses in prompts with square brackets
- **Files Modified**:
  - `scripts/pull-images.bat`: Fixed syntax errors and added comprehensive debugging
  - `scripts/pull-images.sh`: Enhanced with matching debug output and error handling

### Implemented Automatic Default Registry for One-Click Usage
- **Added**: Automatic defaults for non-technical users
- **Changed**: Scripts now default to `vnmw7` registry and `latest` tag without prompting
- **Features**:
  - Double-click the script to automatically pull `vnmw7/suno-frontend:latest` and `vnmw7/suno-backend:latest`
  - No user interaction required - fully automatic operation
  - Clear "AUTOMATIC PULL MODE" banner showing target images
  - Retains parameter support for advanced users: `pull-images.bat custom-registry custom-tag`
  - Environment variable support maintained for CI/CD: `SUNO_IMAGE_REGISTRY` and `SUNO_IMAGE_TAG`
- **Benefits**:
  - Zero-configuration setup for end users
  - Simplified deployment process
  - Non-technical users can deploy with a single double-click
  - Advanced users retain full control via parameters
- **Files Modified**:
  - `scripts/pull-images.bat`: Set `vnmw7` as default registry, removed user prompts
  - `scripts/pull-images.sh`: Set `vnmw7` as default registry, removed user prompts