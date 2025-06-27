# WiFi Fortress - Admin Guide

## Installation on Linux (.deb)
```bash
sudo dpkg -i wifi-fortress_1.0.0_all.deb
```

## Installation on Windows (.exe)
Run the installer and follow on-screen instructions.

## CI/CD with GitHub Actions
- Uses `python-app.yml` in `.github/workflows/`
- Auto-tests and packages project on push

## Module Management
- Drop custom attack modules in `core/plugins/`
- Dynamic loader picks up new Python classes with `run()` method

## Updating
Re-download the latest `.deb` or `.exe` from GitHub Releases or build locally:
```bash
dpkg-deb --build wifi-fortress/
```