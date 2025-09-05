# Backend setup notes

If you see "pyenv: pip: command not found" and the hint that pip exists in certain Python versions, do one of the following:

1. Activate a pyenv Python for your shell (example):
   - pyenv shell 3.13.0
   - python -m pip install --upgrade pip
   - python -m pip install flask flask-socketio flask-cors

2. Or run the provided script (from this folder):
   - chmod +x setup-python.sh
   - ./setup-python.sh 3.13.0

3. If the requested Python is not installed:
   - pyenv install 3.13.0
   - then repeat step 1 or 2.

Using "python -m pip" ensures you call pip for the activated Python rather than relying on a missing shim.
