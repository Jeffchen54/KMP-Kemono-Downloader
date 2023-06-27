@echo off

python -m venv venv && ^
venv\Scripts\activate && ^
pip install -r requirements.txt && ^
move /Y "patch for patoolib\*" venv\Lib\site-packages\patoolib\programs