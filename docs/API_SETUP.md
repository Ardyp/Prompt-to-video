# 🔑 API Setup Guide - Prompt to Video App

## Quick Start (10 minutes)

This guide will get you generating videos in under 10 minutes.

---

## Step 1: Get Google Veo 3.1 API Key

### Option A: Google AI Studio (Recommended - Easiest)

1. **Go to Google AI Studio**
   ```
   https://aistudio.google.com
   ```

2. **Sign in** with your Google account

3. **Click "Get API Key"** in the top right corner

4. **Create a new API key**
   - Click "Create API key"
   - Select "Create API key in new project" (or existing project)
   - Copy the generated key

5. **Enable Billing** (Required for Veo)
   - Go to: https://console.cloud.google.com/billing
   - Link a payment method
   - Veo 3.1 costs: $0.15/sec (Fast) or $0.40/sec (Standard)

### Option B: Third-Party Aggregators (Lower Cost)

If you want cheaper access, these services offer Veo 3 at reduced rates:

| Provider | Cost per 8s Video | Website |
|----------|-------------------|---------|
| fal.ai | ~$1.50 | https://fal.ai/models/fal-ai/veo3 |
| Kie.ai | ~$0.40 (Fast) | https://kie.ai/v3-api-pricing |
| CometAPI | Variable | https://cometapi.com |

---

## Step 2: Get Fish Audio API Key (Voice)

1. **Go to Fish Audio**
   ```
   https://fish.audio
   ```

2. **Create an account** (free)

3. **Navigate to API Settings**
   - Click on your profile → "API Keys"
   - Generate a new API key

4. **Pricing**
   - Free tier: Limited generations for personal use
   - Paid: $9.99/month for 200 minutes (best value)

---

## Step 3: Configure Your App

1. **Copy the environment file**
   ```bash
   cd prompt-to-video-app/backend
   cp .env.example .env
   ```

2. **Edit `.env` with your keys**
   ```bash
   # Open in your editor
   nano .env
   # or
   code .env
   ```

3. **Add your API keys**
   ```env
   # Required for video generation
   GOOGLE_API_KEY=AIzaSy...your_key_here
   
   # Required for voice synthesis
   FISH_AUDIO_API_KEY=sk-...your_key_here
   
   # Provider selection (already set to best options)
   VIDEO_PROVIDER=veo3
   VOICE_PROVIDER=fish_audio
   LANGUAGE_PROVIDER=lingua
   ```

---

## Step 4: Install & Run

### Backend Setup
```bash
# Navigate to backend
cd prompt-to-video-app/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup (in a new terminal)
```bash
# Navigate to frontend
cd prompt-to-video-app/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Step 5: Generate Your First Video! 🎬

### Option A: Use the Web UI
1. Open `http://localhost:5173` in your browser
2. Enter your prompt:
   ```
   Rama Breaks the Shiva's bow in the hall. Theme is Ancient Hindu
   ```
3. Click "Generate Video"
4. Wait 2-5 minutes
5. Download your video!

### Option B: Use the API directly
```bash
curl -X POST http://localhost:8000/api/generation/create \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Rama Breaks the Shivas bow in the hall. Theme is Ancient Hindu",
    "video_duration": 10,
    "aspect_ratio": "16:9",
    "resolution": "1080p",
    "video_style": "cinematic epic ancient Hindu mythology Ramayana"
  }'
```

### Option C: Python Script
```python
import requests
import time

# Create video
response = requests.post(
    "http://localhost:8000/api/generation/create",
    json={
        "prompt": "Rama Breaks the Shivas bow in the hall. Theme is Ancient Hindu",
        "video_duration": 10,
        "resolution": "1080p",
        "video_style": "cinematic ancient Hindu mythology"
    }
)

job_id = response.json()["job_id"]
print(f"Job started: {job_id}")

# Poll for completion
while True:
    status = requests.get(f"http://localhost:8000/api/generation/status/{job_id}").json()
    print(f"Progress: {status['progress']}% - {status['current_step']}")
    
    if status["status"] == "completed":
        result = requests.get(f"http://localhost:8000/api/generation/result/{job_id}").json()
        print(f"\n✅ Video ready: {result['video_url']}")
        break
    elif status["status"] == "failed":
        print(f"❌ Failed: {status['error']}")
        break
    
    time.sleep(5)
```

---

## Troubleshooting

### "API key not valid"
- Make sure you copied the full key
- Check that billing is enabled on Google Cloud
- Verify the key has Veo API access

### "Quota exceeded"
- Check your usage at https://console.cloud.google.com/apis/dashboard
- Request quota increase if needed

### "Video generation timeout"
- Veo can take 2-5 minutes per video
- Ensure stable internet connection
- Try reducing duration or resolution

---

## Cost Calculator

For your "Rama breaks Shiva's bow" video:

| Component | Provider | Calculation | Cost |
|-----------|----------|-------------|------|
| Video (10s) | Veo 3.1 | 10 × $0.40 | $4.00 |
| Voice | Fish Audio | ~70 chars | $0.001 |
| Language | Lingua | Open source | FREE |
| **Total** | | | **$4.00** |

### Monthly Estimates

| Videos/Month | Cost (Veo 3.1) | Cost (Veo Fast) |
|--------------|----------------|-----------------|
| 10 | $40 | $15 |
| 50 | $200 | $75 |
| 100 | $400 | $150 |

---

## Next Steps

1. ✅ API keys configured
2. ✅ App running locally
3. 🎬 Generate your first video
4. 🚀 Deploy to production (see DEPLOYMENT.md)
5. 💰 Set up billing alerts to control costs

---

## Support

- **Google Veo Docs**: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo
- **Fish Audio Docs**: https://fish.audio/docs
- **Issues**: Open a GitHub issue

Happy video generating! 🎥✨
