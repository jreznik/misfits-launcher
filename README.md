# MisfitsLauncher

MisfitsLauncher is a hardware-accelerated, controller-first game launcher designed specifically for the Steam Deck and SteamOS.

## Motivation
The primary goal of this project was to create a launcher that provides a native Steam Deck look and feel, optimized for touchscreen and physical controller navigation. It is designed to be a simple, lightweight bridge for alternative game stores without the complexity of larger tools.

**Note:** This is not intended as a competitor to established launchers like Heroic or Lutris. For advanced configuration, complex prefix management, or broader compatibility, users should continue to use those excellent tools.

## Current Status
**MisfitsLauncher is under active development.** 
Currently, it features stable integration with the Epic Games Store and UMU-run for game execution.

## Features
- **Native SteamOS UI:** High-fidelity $1280 \times 800$ layout with hardened D-pad focus engine.
- **Epic Games Integration:** Seamless library sync and authentication using the `legendary` CLI.
- **Dynamic Backgrounds:** Immersive selection-based artwork transitions.
- **ProtonDB Integration:** Real-time Steam Deck compatibility ratings and badges.
- **Download Manager:** Background installation queue with pause/resume support.
- **UMU Management:** Integrated tool for managing Proton runtimes and GE-Proton installation.
- **Flatpak Ready:** Distributed as a portable, sandboxed bundle.

## Installation (Flatpak)
```bash
flatpak install MisfitsLauncher.flatpak
```

## Running Natively (Development)
Ensure you have `PySide6`, `legendary-gl`, and `umu-run` installed on your host system.
```bash
python3 main.py
```

## Authors
- **Jaroslav Reznik** (Author)
- Assisted by **Antigravity**
