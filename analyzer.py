"""Analyze Reddit Users on their behavior"""

import json
import argparse
import requests
import datetime
from operator import itemgetter
from ascii_graph import Pyasciigraph
from ascii_graph.colors import Gre, Yel, Red
from ascii_graph.colordata import hcolor
import re
import numpy
import sys
import colorama
import shelve
import time
import dbm

__version__ = '1.1.0'

#For correct color output on windows
colorama.init()

#Parse arguments
parser = argparse.ArgumentParser(description=
    "Reddit Account Analyzer (https://github.com/rafficer/reddit-analyzer) Version %s" % __version__,
usage='%(prog)s -u <username> [options]')
parser.add_argument("-u", "--user", required=True, help="Reddit account username")
parser.add_argument("-t", "--top",type=int, help="Specifies how many entries per top list. \"0\" outputs all entries of a toplist. Default: 5")
parser.add_argument("-w", "--watson", action='store_true', help="Queries IBM Watson Personality Insights")
parser.add_argument("-r", "--subreddit", help="Prints links to all submissions/comments of user to that specific subreddit")

args = parser.parse_args()

def apirequest(url):
    request_headers = {
    "Accept-Language": "en-US,en;q=0.5",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://reddit.com",
    "Connection": "keep-alive" 
    }

    res = requests.get(url, headers=request_headers)

    return res.json()


# Returns a list of dictionaries with either all comments or all submissions
def populate_dics(username, option):
    switch = {
        "c" : "comments",
        "s" : "submitted"
    }

    switch2 = {
        "c" : "comments",
        "s" : "posts"
    }

    url = f"https://api.reddit.com/user/{username}/{switch[option]}?limit=100&after="
    lst = []
    total = 0
    name = ""

    print()
    print('\033[93m' + f"Fetching {switch2[option]}..." + '\033[0m')

    while True:
        data = apirequest(url + name)
        num = int(data['data']['dist'])
        total += num
        if num == 0:
            break
        for entry in data['data']['children']:
            lst.append(entry)
        name = data['data']['children'][num - 1]['data']['name']
        print('\033[93m' + "Fetched %d %s" % (total, switch2[option]) + '\033[0m', end="\r")
    return lst
        

# Sort data descending counts
def sort_data(dic):
    sorted_list = [[],[],[]]
    for pair in reversed(sorted(dic.items(), key=itemgetter(1))):
        sorted_list[0].append(pair[0])
        sorted_list[1].append(pair[1])
    return sorted_list


def print_stats(statlist, statname):
    #statlist is a list containing 2 lists, looking like this: [[namelist],[valuelist]] e.g [["AskReddit", "TIL"],[5,6]]
    helperlist = []
    if args.top == 0:
        top = len(statlist[0])
    elif args.top != None:
        top =  args.top
    else:
        top = 5
    if top > len(statlist[0]):
        top = len(statlist[0])

    for x in statlist[0]:
        helperlist.append(len(x))
    maxlen_name = max(helperlist) + 10
    helperlist = []
    for x in statlist[1]:
        helperlist.append(len(str(x)))
    maxlen_value = max(helperlist) + 2
    print('\033[92m' + "[+]", statname)
    print("[+] Datapoints:", sum(statlist[1]), end="")
    print("| Total Entries:", len(statlist[1]), end="")
    print("| Showing:", top, end="")
    print('\033[0m')
    for x in range(top):
        
        print("- ", ("{:<%d}" % maxlen_name).format(statlist[0][x]), end="") # Name
        print(":", end="")
        print(("{:>%d}" % maxlen_value).format(statlist[1][x]), end="") # Value
        print("|", end="")
        print("(%.1f%%)" % (float(statlist[1][x]) / sum(statlist[1]) * 100)) #Percentage

def filter_data(lst, keyname):
    dic = {}
    for entry in lst:
        domain = entry['data'][keyname]

        if domain not in dic.keys():
                dic[domain] = 1
        else:
            dic[domain] += 1
    return dic

def difference_from_unixtime(timestamp):
    unixinnormal = datetime.datetime.utcfromtimestamp(timestamp)
    current_time = datetime.datetime.utcnow()
    d = (current_time - unixinnormal)
    days = d.days
    seconds = d.seconds

    years = int(days / 365)
    days -= int(years * 365)

    hours = int(seconds / 3600)
    seconds -= int(3600 * hours)
    minutes = int(seconds / 60)
    seconds -= int(60 * minutes)
    if years <= 0:
        if days <= 0:
            if hours <= 0:
                if minutes <= 0:
                    return "%s seconds" % seconds
                return "%s hours" % str(minutes).zfill(2)
            return "%s:%s hours" % (str(hours).zfill(2), str(seconds).zfill(2))
        return "%d days, %s:%s hours" % (days, str(hours).zfill(2), str(minutes).zfill(2))
    else:
        return "%d Years, %d days, %s:%s hours" % (years, days, str(hours).zfill(2), str(minutes).zfill(2))

# The following two functions were copied from https://github.com/x0rz/tweets_analyzer and just slightly modified to fit my needs
def print_charts(dataset, title, weekday=False):
    """ Prints nice charts based on a dict {(key, value), ...} """
    chart = []
    keys = sorted(dataset.keys())
    mean = numpy.mean(list(dataset.values()))
    median = numpy.median(list(dataset.values()))

    for key in keys:
        if (dataset[key] >= median * 1.33):
            displayed_key = "%s (\033[92m+\033[0m)" % (int_to_weekday(key) if weekday else key)
        elif (dataset[key] <= median * 0.66):
            displayed_key = "%s (\033[91m-\033[0m)" % (int_to_weekday(key) if weekday else key)
        else:
            displayed_key = (int_to_weekday(key) if weekday else key)
        
        chart.append((displayed_key, dataset[key]))

    thresholds = {
        int(mean): Gre, int(mean * 2): Yel, int(mean * 3): Red,
    }

    data = hcolor(chart, thresholds)

    graph = Pyasciigraph(
        separator_length=4,
        multivalue=False,
        human_readable='si',
    )

    for line in graph.graph(title, data):
        print(line)
    print("")

def int_to_weekday(day):
    weekdays = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
    return weekdays[int(day) % len(weekdays)]

def print_activity_charts(commentlist, submissionlist):
    hourdic = {
        "00:00" : 0,
        "01:00" : 0,
        "02:00" : 0,
        "03:00" : 0,
        "04:00" : 0,
        "05:00" : 0,
        "06:00" : 0,
        "07:00" : 0,
        "08:00" : 0,
        "09:00" : 0,
        "10:00" : 0,
        "11:00" : 0,
        "12:00" : 0,
        "13:00" : 0,
        "14:00" : 0,
        "15:00" : 0,
        "16:00" : 0,
        "17:00" : 0,
        "18:00" : 0,
        "19:00" : 0,
        "20:00" : 0,
        "21:00" : 0,
        "22:00" : 0,
        "23:00" : 0
    }
    weekdaydic = {
        0 : 0,
        1 : 0,
        2 : 0,
        3 : 0,
        4 : 0,
        5 : 0,
        6 : 0
    }

    if len(commentlist) > 0:
        for comment in commentlist:
            time = datetime.datetime.utcfromtimestamp(comment['data']['created_utc'])
            hour = str(time.hour).zfill(2) + ":00"
            weekdaydic[time.weekday()] += 1
            hourdic[hour] += 1

    if len(submissionlist) > 0:
        for submission in submissionlist:
            time = datetime.datetime.utcfromtimestamp(submission['data']['created_utc'])
            hour = str(time.hour).zfill(2) + ":00"
            weekdaydic[time.weekday()] += 1
            hourdic[hour] += 1
    
    print_charts(hourdic, "Daily activity by hour")
    print()
    print_charts(weekdaydic, "Weekly activity by day", True)
    print()

def print_average_upvotes(commentlist, submissionlist):
    commentscores = []
    subscores = []
    if len(commentlist) > 0:
        for comment in commentlist:
            commentscores.append(comment['data']['score'])
        print("Average Score on comments:", "%.1f" % average(commentscores))

    if len(submissionlist) > 0:
        for sub in submissionlist:
            subscores.append(sub['data']['score'])
        print("Average Score on submissions:", "%.1f" % average(subscores))


def average(lst):
    return float(sum(lst)) / len(lst)

def print_subreddit_links(commentlist, submissionlist):
    print()
    print()
    commentlinks = []
    sublinks = []

    if len(commentlist) > 0:
        for comment in commentlist:
            if comment['data']['subreddit'] == args.subreddit:
                commentlinks.append(comment['data']['permalink'])

    if len(submissionlist) > 0:
        for sub in submissionlist:
            if sub['data']['subreddit'] == args.subreddit:
                sublinks.append(sub['data']['permalink'])

    if len(commentlinks) > 0:
        print("Links to comments in /r/" + args.subreddit)
        for x in commentlinks:
            print("https://www.reddit.com" + x)
    else:
        print("No comments in /r/" + args.subreddit)

    if len(sublinks) > 0:
        print("Links to submissions in /r/" + args.subreddit)
        for x in sublinks:
            print("https://www.reddit.com" + x)
    else:
        print("No submissions in /r/" + args.subreddit)

def watson(commentlist, submissionlist):
    print()
    from watson_developer_cloud import PersonalityInsightsV2 as PersonalityInsights
    from IBM_Watson import PIusername, PIpassword

    if PIusername == '' or PIpassword == '':
        print("Watson Analysis was requested, but the password and username seem to be empty")
        return

    print('\033[92m' + "[+] IBM Watson Personality Insights Results" + '\033[0m')

    def flatten(orig):
        data = {}
        for c in orig['tree']['children']:
            if 'children' in c:
                for c2 in c['children']:
                    if 'children' in c2:
                        for c3 in c2['children']:
                            if 'children' in c3:
                                for c4 in c3['children']:
                                    if (c4['category'] == 'personality'):
                                        data[c4['id']] = c4['percentage']
                                        if 'children' not in c3:
                                            if (c3['category'] == 'personality'):
                                                    data[c3['id']] = c3['percentage']
        return data

    text = ""

    for comment in commentlist:
        text += comment['data']['body']
    

    personality_insights = PersonalityInsights(username=PIusername, password=PIpassword)
    pi_result = personality_insights.profile(text)

    flattened_result = flatten(pi_result)

    helperlist = []
    for key in flattened_result.keys():
        helperlist.append(len(key))
    
    maxlen_key = max(helperlist)

    for key in flattened_result.keys():
        print("- ", ("{:<%d}" % maxlen_key).format(key), ":", end="")
        value = "%.1f%%" % (flattened_result[key] * 100)
        print(("{:>4}").format(value))
    
      
# Get and print general account information
accountstats = apirequest(f"https://api.reddit.com/user/{args.user}/about")
print('\033[92m' + "--General Information about the Account--", '\033[0m')
print("Accountname:", accountstats['data']['name'])
print()
total_karma = int(accountstats['data']['comment_karma']) + int(accountstats['data']['link_karma'])
print("Total Karma:", total_karma)
if total_karma != 0:
    print("Comment Karma:", accountstats['data']['comment_karma'], "|", "(%.1f%%)" % (float(accountstats['data']['comment_karma']) / total_karma * 100))
    print("Post Karma:", accountstats['data']['link_karma'], "|", "(%.1f%%)" % (float(accountstats['data']['link_karma']) / total_karma * 100))
print()
print("Account created:", datetime.datetime.utcfromtimestamp(accountstats['data']['created_utc']), "UTC")
print("Account Age:", difference_from_unixtime(accountstats['data']['created_utc']))

# Get comments/submissions and print information from them
# Use shelffile for it to not fetch again and again

def new_shelffile():
    shelffile = shelve.open(f"{args.user}.shelf",)
    comments = populate_dics(args.user, "c")
    submissions = populate_dics(args.user, "s")
    shelffile['comments'] = comments
    shelffile['submissions'] = submissions
    shelffile['time'] = time.time()
    shelffile.close()
    return comments, submissions
try: #Use existing Shelffile
    shelffile = shelve.open(f"{args.user}.shelf", "w")
    if time.time() - shelffile['time'] >= 900: # If the shelffile is older than 15 minutes, create a new one
        comments, submissions = new_shelffile()
    else:
        comments = shelffile['comments']
        submissions = shelffile['submissions']
        shelffile.close()
except dbm.error: #Create new Shelffile
    comments, submissions = new_shelffile()
    

def usermain():
    print()
    print()
    print_activity_charts(comments, submissions)
    if len(comments) > 0:
        print_stats(sort_data(filter_data(comments, "subreddit")), "Top active subreddits based on comments")
        print()
    if len(submissions) > 0:
        print_stats(sort_data(filter_data(submissions, "subreddit")), "Top active subreddits based on posts")
        print()
    if len(submissions) > 0:
        print_stats(sort_data(filter_data(submissions, "domain")), "Top domains posted")
        print()
    if len(comments) > 0:
        print_stats(sort_data(filter_data(comments, "link_author")), "Top people replied to")
        print()

    print_average_upvotes(comments, submissions)
    if args.watson:
        watson(comments, submissions)

if args.subreddit == None:
    usermain()
else:
    print_subreddit_links(comments, submissions)
