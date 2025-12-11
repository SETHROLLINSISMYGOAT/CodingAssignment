How to Run
Provide clear, step-by-step instructions:

Prerequisites: Python 3.x.

Setup:

Bash

git clone [https://github.com/SETHROLLINSISMYGOAT/CodingAssignment.git]
cd [CodingAssignment]
python -m venv venv
.\venv\Scripts\Activate.ps1   # Use 'source venv/bin/activate' on Linux/macOS
pip install -r requirements.txt
Run Server:

Bash

python -m uvicorn app.main:app --reload
Testing:checking http://127.0.0.1:8000/docs for interactive API testing.
