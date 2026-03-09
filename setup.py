import subprocess, sys

print("Installing Python packages...")
subprocess.run([sys.executable, '-m', 'pip', 'install',
    'gradio', 'plotly', 'pandas', 'beautifulsoup4',
    'playwright', 'nest_asyncio'], check=True)

print("Installing Playwright Chromium browser...")
subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium', '--with-deps'], check=True)

print("\n✅ Setup complete! Now run:  python app.py")