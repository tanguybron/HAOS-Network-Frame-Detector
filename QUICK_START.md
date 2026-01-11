# Quick Start Guide

## Publishing to GitHub (5 minutes)

```bash
# 1. Initialize git
git init
git add .
git commit -m "Initial commit: Network Frame Detector integration"

# 2. Create repository on GitHub (via web interface)
#    - Go to github.com → New repository
#    - Name: HAOS-Network-Frame-Detector
#    - Public repository
#    - Don't initialize with README

# 3. Push to GitHub (replace USERNAME)
git remote add origin https://github.com/USERNAME/HAOS-Network-Frame-Detector.git
git branch -M main
git push -u origin main

# 4. Create release on GitHub
#    - Go to repository → Releases → Create new release
#    - Tag: v1.0.0
#    - Title: v1.0.0
#    - Publish release
```

## Installing on HAOS via HACS (2 minutes)

1. **Open HACS** in Home Assistant
2. **Integrations** → Three dots (⋮) → **Custom repositories**
3. Add: `https://github.com/USERNAME/HAOS-Network-Frame-Detector` (category: Integration)
4. **Search** for "Network Frame Detector" → **Download**
5. **Restart** Home Assistant
6. **Settings** → **Devices & Services** → **Add Integration** → "Network Frame Detector"

## Installing on HAOS Manually (5 minutes)

### Option A: Via SSH

```bash
# Connect to HAOS
ssh root@<your-haos-ip>

# Clone repository
cd /config/custom_components
git clone https://github.com/USERNAME/HAOS-Network-Frame-Detector.git temp
cp -r temp/custom_components/network_frame_detector .
rm -rf temp

# Restart Home Assistant
ha core restart
```

### Option B: Via Samba

1. Enable **Samba** add-on in Home Assistant
2. Map network drive: `\\<your-haos-ip>\config`
3. Navigate to `custom_components\`
4. Create `network_frame_detector` folder
5. Copy all files from `custom_components/network_frame_detector/`
6. Restart Home Assistant

## First Configuration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **"Network Frame Detector"**
4. Configure:
   - **Name**: `Google Cast Discovery`
   - **Protocol**: `UDP`
   - **Port**: `5353`
   - **Multicast**: `true`
   - **Pattern Type**: `string`
   - **Pattern Value**: `_googlecast._tcp.local`
   - **Cooldown**: `5` seconds
   - **Sensor Duration**: `30` seconds

5. The binary sensor will appear and turn ON when Google Cast devices are detected!

## Troubleshooting

- **Not appearing?** → Check `/config/custom_components/network_frame_detector/` exists
- **Import errors?** → Check Home Assistant logs
- **Port in use?** → Try a different port number
- **HACS not finding it?** → Ensure repository is public and has a release tag

For detailed instructions, see [PUBLISHING.md](PUBLISHING.md).

