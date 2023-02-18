# bridge_server

This personal project consists on a Asynchronous Server that acts as a bridge and allows the connected clients to communicate between them with messages. 
The scope of this project is to test cloud integration, in AWS, with a simple server running. So the server will be hosted in aws and the clients will connect to it using the assigned **IP** and **PORT**

# Setup

This project has some dependencies that need to be met. For installation, feel free to use a [Python Venv](https://docs.python.org/3/library/venv.html) and execute the following command:

```
pip install -r requirements.txt
```

# Github actions

To implement a Agile methodology and some steps of CI/CD, I decided to implement to Github Actions to improve our workflow. One is for running tests and building the code and the other is for auto-generating documentation. They can be found in the projects `Actions` tab.

## Tests

To guarantee good development and functioning of the system, I decided to implement tests using the [pytest framework](https://docs.pytest.org/en/7.2.x/). This tests can be found at the `tests` directory and can be executed by simply running:

```
pytest
```

## Documentation

Documentation is a special part of any project, so in every package, class and methods created, I made sure to write good comments and information that can be easily updated, auto-generated and compiled into one easily readable file. For that, I chose the [pdoc3](https://pypi.org/project/pdoc3/) auto documentation tool. With this tool I just needed to write comments in the [google styleguide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) and those comments were then compiled into html files. Once a commit is executed the github action will auto generate the documentation and upload it to the `docs/assignment-2---bingo-19` folder, where it can be executed via a browser.

* If you wish to manually execute the auto-documentation, execute the following command:
  ```
  pdoc3 --html --force -o ./docs .
  ```
* To open the documentation, go to the folder and execute it with your browser of choice, for example
  ```
  brave-browser index.html
  ```

# Get-Started

## Localy

## AWS


# Logs

As you can see, if you execute the project at least once, both in the client and server, a `logs` folder will appear. In this folder, you can check the logs by yourself, to view the exchanged information betweem the client and server, as well as their responses and decisions.

If you execute the programs a lot of times, a sizable ammount of log files may be created. To assist in that, I created a simple bash script that automatically removes all the log files. You can execute by introducing the following command:

```
bash clear_logs.sh
```

# Notes

Attention to the name of the clients when launching