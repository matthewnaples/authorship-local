# authorship-local

 Instructions to run Authorship Local for the demo.

 1. clone the repo
 2. Open Command Prompt on your windows computer
 3. In the working directory, create a virtual environment `python -m venv venv`
 4. install requirements `pip install -r requirements.txt`
 5. create the executable: `pyinstaller authorship.spec`
 6. run the chainlit UI Server: `chainlit run app.py`
 7. Now you may click the executable file. This will not work unless you've got the chainlit server running.

The executable just launches a window and connects to the localhost where chainlit is running. For demo purposes, the chainlit server must run in a hidden command prompt.
