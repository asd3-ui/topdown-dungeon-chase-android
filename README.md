# Top-Down Dungeon Chase (Android APK Engine)

A production-ready, crash-proof Top-Down 2D/2.5D Dungeon Chase game built in Python and Pygame, optimized for Android deployment via Buildozer.

## Game Highlights
- **Top-Down Perspective (منظر من الاعلى)**: Full panoramic awareness with dynamic camera follow and tactical overview modes.
- **Analog Multi-Touch Virtual Joystick**: Circular border with centered touch-sensitive knob.
- **30-Frame Throttled A* AI**: Enemy hunts player relentlessly through corridor loops.
- **Zero-Font Architecture**: 100% vector drawn HUD with `pygame.draw` to prevent Android system font crashes.
- **Physical Android Back Button**: Traps `pygame.K_AC_BACK` cleanly without crash.

## Building the APK
### Option A: GitHub Actions (Recommended)
1. Push this repository to GitHub.
2. The included `.github/workflows/build-apk.yml` builds and uploads your APK artifact.

### Option B: Local Linux / WSL2
```bash
pip install buildozer cython==0.29.36
buildozer android debug
```
