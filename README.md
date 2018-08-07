# Reddit Account Analyzer

A tool to analyze a reddit account based on their submissions and comments. The tool prints back the following information:

* Karma Scores
* Account creation date and age
* Average activity by hour and by day of the week
* Top active subreddits by comments and by submissions
* Top domains posted/sites linked to
* Top people replied to
* Average Score on Comments and Submissions
* Links to comments/submissions in a specified subreddit

Please feel free to contribute, raise issues or request features!

### Installation

Written in Python 2.7.

`git clone https://github.com/rafficer/reddit-analyzer` or download as zip.

Install the requirements:

* ascii_graph
* numpy
* colorama

`pip install -r requirements.txt`

If you want to use IBM Watson Personality Insights (-w option) also do:

`pip install -r watson_requirements.txt`

### Usage

``` Python
usage: analyzer.py -u <username> [options]

Reddit Account Analyzer (https://github.com/rafficer/reddit-analyzer) Version
1.1.0

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  Reddit account username
  -t TOP, --top TOP     Specifies how many entries per top list. "0" outputs
                        all entries of a toplist. Default: 5
  -w, --watson          Queries IBM Watson Personality Insights
  -r SUBREDDIT, --subreddit SUBREDDIT
                        Prints links to all submissions/comments of user to
                        that specific subreddit
```

### Example

![x](https://i.imgur.com/heR9B4w.gif)

*Idea and 2 functions from https://github.com/x0rz/tweets_analyzer*
