# authorship-local

todo : add chainlit secret to env. Instructions to run Authorship Local for the
demo. 0. Make sure Ollama is installed and that you have pulled the model
`llama3.1:8b`. You can pull the model via `ollama pull llama3.1:8b` command

## Steps to run the project (for Nils SXSW)
1. Open Command Prompt on your windows computer
2. go to the project directory `cd Desktop\authorship-local`
3. start the virtual environment:  `venv\Scripts\activate`
4. run the chainlit UI Server: `chainlit run app.py --headless`

Once the chainlit server is up and running, you can double click the Authorship exe icon that's on the desktop




## Steps to get the project running (if you haven't yet cloned)
1. clone the repo
2. Open Command Prompt on your windows computer
3. In the working directory, create a virtual environment `python -m venv venv`
4. activate the virtual environment. `venv\Scripts\activate`
5. install requirements `pip install -r requirements.txt`
6. create the executable: `pyinstaller authorship.spec`
7. run the chainlit UI Server: `chainlit run app.py --headless`
8. Now you may click the executable file. This will not work unless you've got
   the chainlit server running.

The executable just launches a window and connects to the localhost where
chainlit is running. For demo purposes, the chainlit server must run in a hidden
command prompt.
