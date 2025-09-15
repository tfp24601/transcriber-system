# Development Notes & Context

## 👤 About Ben (The User)

**Background:**
- **Not a coder** but **tech-savvy** with strong IT background
- **Excellent vibe-coding partner** - understands systems and concepts well
- **Self-hosting enthusiast** with sophisticated home infrastructure
- **Prefers incremental approach** - build working prototypes first, then expand

**Communication Style:**
- Needs **hand-holding with explanations** for coding concepts
- Appreciates **why** things are done a certain way, not just **what**
- Prefers **practical examples** over abstract theory
- Values **working but secure solutions** over perfect code

**Technical Environment:**
- **Sol Workstation**: Ubuntu 24.04, RTX 4090, 128GB RAM, Ryzen 9 7950X
- **Existing Stack**: Docker Compose with n8n, PostgreSQL, Caddy, many services
- **Network**: Cloudflare Access + Caddy reverse proxy via Lunanode4 VPS
- **Domain Pattern**: `*.solfamily.group` subdomains for services

## 🏗️ Architecture Preferences

**Established Patterns:**
- **Docker-first**: Everything containerized with docker-compose.yml
- **Simple web apps**: Like formatter app - single HTML file with embedded CSS/JS
- **Existing infrastructure**: Leverages postgres, n8n, caddy already running
- **Privacy-focused**: Avoids third-party services when possible, prefers self-hosted and FOSS solutions
- **Mobile-friendly**: But server-first architecture (not native mobile apps)

**This Project's Evolution:**
- Started with **simple version first** (web upload only)
- Built with **future extensibility** in mind (Cloudflare Access ready)
- Chose **TypeScript/React** for maintainability (Ben's first React project!)
- **GPU-accelerated** backend leveraging existing RTX 4090

## 🔧 Development Approach

**When Working Together:**
1. **Start simple** - Get basic functionality working first
2. **Explain concepts** - Why we're using certain technologies
3. **Show examples** - Practical code with comments explaining purpose  
4. **Test incrementally** - Build → test → iterate
5. **Document everything** - Ben values good documentation for future reference

**Problem-Solving Style:**
- **Troubleshoot methodically** - Check logs, test endpoints, verify configs
- **Provide specific commands** - Exact bash commands with explanations
- **Multiple approaches** - Show alternatives when things don't work
- **Error context** - Explain what errors mean and why they happen

## 📋 Current System Status

**What's Built (September 9, 2025):**
- ✅ Complete transcriber system from BuildSpec.md requirements
- ✅ Web PWA, Android app, iOS shortcuts, n8n workflows, database schema
- ✅ Ready for deployment following docs/DEPLOYMENT.md
- ✅ Uses Ben's existing infrastructure patterns

**Deployment Status:**
- 🟡 **Not yet deployed** - Ben will follow DEPLOYMENT.md guide
- 🟡 **Testing needed** - Full workflow from mobile recording to transcript
- 🟡 **Cloudflare Access** - Simple auth first, CF Access integration later

**Known Considerations:**
- **Hugging Face token** needed for WhisperX diarization models
- **GPU memory** management for concurrent transcriptions
- **File cleanup** strategy for long-term storage management
- **Mobile app distribution** (Android APK signing, iOS TestFlight considerations)

## 🚨 Important Reminders for Future Sessions

**Always Remember:**
- Ben is **learning as we go** - explain new concepts clearly
- **Practical over perfect** - working, secure solutions beat elegant theory
- **Follow existing patterns** - integrate with Sol infrastructure, don't reinvent unless necessary or there is clearly a superior way
- **Document changes** - Update relevant .md files when modifying system
- **Test incrementally** - small steps, verify each works before moving on

**Project Context:**
- This replaces typing personal and meeting notes manually
- Vision: "one-tap record → send → read transcript" on mobile
- Privacy-first: no Otter.ai, no cloud services
- Multi-user: family members will use it too
- Built for **actual daily use**, not just a proof of concept

**Files to Check First:**
- `BuildSpec.md` - Original requirements and vision
- `README-PROJECT-COMPLETE.md` - Current system overview
- `docs/DEPLOYMENT.md` - Where Ben will start next
- Recent git commits - What was last changed/added

## 🎯 Success Metrics

**The system succeeds when:**
- Ben can record a meeting on phone → transcript appears in web UI
- Family members can use it without technical setup
- Transcripts are accurate enough to replace manual note-taking
- System runs reliably without constant maintenance
- Ben understands how to troubleshoot and extend it

---

*Remember: Ben built this system to solve a real daily problem. Keep solutions practical, explanations clear, and always test that things actually work end-to-end!*