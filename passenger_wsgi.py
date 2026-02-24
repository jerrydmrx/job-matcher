import sys
import os
import traceback

project_dir = os.path.dirname(__file__)
sys.path.insert(0, project_dir)

# If a virtual environment exists at .venv, add its site-packages to sys.path
venv_dir = os.path.join(project_dir, '.venv')
if os.path.isdir(venv_dir):
	py_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
	candidate = os.path.join(venv_dir, 'lib', py_version, 'site-packages')
	if os.path.isdir(candidate):
		sys.path.insert(0, candidate)
	else:
		# Windows venv layout
		win_candidate = os.path.join(venv_dir, 'Lib', 'site-packages')
		if os.path.isdir(win_candidate):
			sys.path.insert(0, win_candidate)

# Import the Flask app and capture any import-time errors to a log file
try:
	from app import app as application
except Exception:
	tb = traceback.format_exc()
	log_file = os.path.join(project_dir, 'passenger_error.log')
	try:
		with open(log_file, 'a') as f:
			f.write(tb + '\n')
	except Exception:
		# If we cannot write the log, print to stderr as a last resort
		sys.stderr.write(tb)
	# Re-raise so the WSGI server still fails, but we now have the traceback saved
	raise