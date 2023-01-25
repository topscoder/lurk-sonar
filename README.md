# Lurk all source code from a SonarQube instance

Because we can.

## When do you need this?

* If you have access to a SonarQube instance
* You want to perform deep analysis on the projects in this instance
* You cannot access the source code directly to download
* You are a bug bounty hunter
* There's too much code to download one by one by hand

## Usage

1. Clone this repository
2. `cd sonar-lurk`
3. `pip3 install -r requirements.txt`
4. `cp .settings.json.example .settings.json`
5. Set target URL, username and password in `.settings.json`
6. Run `python3 lurk.py`
7. Sit back and relax 💤