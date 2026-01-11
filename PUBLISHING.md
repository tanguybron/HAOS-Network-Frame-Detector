# Publishing and Installation Guide

## Publishing to GitHub

### Step 1: Initialize Git Repository

```bash
# Navigate to the project directory
cd /Users/tanguybron/Documents/Dev/HAOS-Network-Frame-Detector

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Network Frame Detector integration"
```

### Step 2: Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" icon in the top right → "New repository"
3. Repository name: `HAOS-Network-Frame-Detector` (or your preferred name)
4. Description: "Secure network frame detector integration for Home Assistant"
5. Choose **Public** (required for HACS)
6. **Do NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

### Step 3: Push to GitHub

```bash
# Add remote (replace USERNAME with your GitHub username)
git remote add origin https://github.com/USERNAME/HAOS-Network-Frame-Detector.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

### Step 4: Create a Release (for HACS)

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `v1.0.0`
5. Description: "Initial release of Network Frame Detector integration"
6. Click "Publish release"

## Installing on Home Assistant OS (HAOS)

### Method 1: HACS Installation (Recommended)

HACS (Home Assistant Community Store) is the easiest way to install custom integrations.

#### Prerequisites

1. Install HACS if not already installed:
   - Go to [HACS Installation](https://hacs.xyz/docs/setup/download)
   - Follow the installation instructions for HAOS

#### Installation Steps

1. Open Home Assistant
2. Go to **HACS** in the sidebar
3. Click **Integrations**
4. Click the three dots menu (⋮) in the top right
5. Select **Custom repositories**
6. Add repository:
   - **Repository**: `https://github.com/USERNAME/HAOS-Network-Frame-Detector`
   - **Category**: `Integration`
   - Click **Add**
7. Close the dialog
8. In HACS Integrations, search for **"Network Frame Detector"**
9. Click on it and then click **Download**
10. **Restart Home Assistant** (Settings → System → Restart)
11. After restart, go to **Settings → Devices & Services**
12. Click **Add Integration**
13. Search for **"Network Frame Detector"** and configure your first detection rule

### Method 2: Manual Installation

If you prefer not to use HACS or want to test before publishing:

#### Step 1: Access HAOS Filesystem

1. Enable SSH add-on in Home Assistant:
   - Go to **Settings → Add-ons → Add-on Store**
   - Install **SSH & Web Terminal** add-on
   - Configure and start it

2. Connect via SSH:
   ```bash
   ssh root@<your-haos-ip>
   ```

#### Step 2: Copy Integration Files

```bash
# Navigate to custom_components directory
cd /config/custom_components

# Create directory if it doesn't exist
mkdir -p network_frame_detector

# Copy files (from your local machine)
# Option A: Use SCP from your local machine
scp -r /Users/tanguybron/Documents/Dev/HAOS-Network-Frame-Detector/custom_components/network_frame_detector/* root@<your-haos-ip>:/config/custom_components/network_frame_detector/

# Option B: Use git clone (if you've published to GitHub)
cd /config/custom_components
git clone https://github.com/USERNAME/HAOS-Network-Frame-Detector.git temp
cp -r temp/custom_components/network_frame_detector .
rm -rf temp
```

#### Step 3: Restart Home Assistant

1. Go to **Settings → System → Restart**
2. Or via SSH: `ha core restart`

#### Step 4: Add Integration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **"Network Frame Detector"**
4. Configure your detection rule

### Method 3: Using Samba Share (Easier Manual Method)

If you have Samba share enabled:

1. Enable Samba add-on in Home Assistant
2. Map the network drive on your computer
3. Navigate to `\\<your-haos-ip>\config\custom_components\`
4. Create `network_frame_detector` folder
5. Copy all files from `custom_components/network_frame_detector/` to the folder
6. Restart Home Assistant

## Verifying Installation

After installation, verify the integration is working:

1. Check logs:
   - Go to **Settings → System → Logs**
   - Look for "Network Frame Detector" entries
   - Should see: "Setting up network_frame_detector"

2. Check integration:
   - Go to **Settings → Devices & Services**
   - You should see "Network Frame Detector" in the list
   - Click on it to see your configured detection rules

3. Test detection:
   - Configure a detection rule (e.g., Google Cast mDNS)
   - The binary sensor should appear in **Developer Tools → States**
   - Search for `binary_sensor.<your_rule_name>`

## Troubleshooting

### Integration Not Appearing

- **Check file structure**: Ensure files are in `/config/custom_components/network_frame_detector/`
- **Check permissions**: Files should be readable by Home Assistant
- **Check logs**: Look for import errors in Home Assistant logs
- **Restart**: Always restart Home Assistant after manual installation

### HACS Not Finding Integration

- **Check repository URL**: Must be public and accessible
- **Check manifest.json**: Must be valid JSON
- **Check release**: HACS prefers tagged releases
- **Clear HACS cache**: HACS → Settings → Clear HACS cache

### Port Already in Use

- **Check other integrations**: Another integration might be using the port
- **Check system services**: Some HAOS services use common ports
- **Use different port**: Try a different port number

### Permission Denied Errors

- **Check HAOS permissions**: Integration should work with standard permissions
- **Check firewall**: HAOS firewall shouldn't block local traffic
- **Check port binding**: Some ports require elevated permissions (avoid ports < 1024)

## Updating the Integration

### Via HACS

1. Go to **HACS → Integrations**
2. Find **Network Frame Detector**
3. Click **Update** if available
4. Restart Home Assistant

### Manual Update

1. Stop the integration (remove config entries temporarily)
2. Replace files in `/config/custom_components/network_frame_detector/`
3. Restart Home Assistant
4. Re-add your configuration entries

## Publishing Updates to GitHub

```bash
# Make your changes
# ...

# Commit changes
git add .
git commit -m "Description of changes"

# Push to GitHub
git push origin main

# Create new release (for HACS)
# Go to GitHub → Releases → Create new release
# Tag: v1.0.1 (increment version)
# Update manifest.json version before releasing
```

## HACS Requirements

For HACS to recognize your integration:

1. ✅ Repository must be **public**
2. ✅ Must have a **valid `manifest.json`**
3. ✅ Must have a **README.md**
4. ✅ Recommended: Create a **release/tag** (e.g., `v1.0.0`)
5. ✅ Integration must be in `custom_components/<domain>/` structure

Your integration already meets all these requirements! 🎉

