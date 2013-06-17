import json
import urllib2
import base64
import pprint
import datetime

#move to a model
username = 'jbonnett'
password = ''
mileston = 2
repo_user = 'Jbonnett'
repo_name = 'github-on-fire'
iteration_length = datetime.timedelta(weeks=1).total_seconds()

#move to a model
label_point_map = {
        '1hr': 1,
        '1d': 5,
        '1w': 25,
    }

#assumed burn rate
BR = 75
iteration_length = datetime.timedelta(weeks=1).total_seconds()

def get_issues(state="open"):
    #get all the github issues
    req = urllib2.Request(url="https://api.github.com/repos/%s/%s/issues?state=%s&sort=created&direction=asc&milestone=2&per_page=300" % (repo_user, repo_name, state))
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    req.add_header("Authorization", "Basic %s" % base64string)
    return json.load(urllib2.urlopen(req))


def generate_burngraph():
    #issues must be ordered by creation date.
    data = {}
    #Convert dates to weeks out from start
    start_date = ""
    for state in ('closed', 'open'):
        issues = get_issues(state)
        if state == "closed":
            #barf.pprint(issues)
            start_date = datetime.datetime.strptime(issues[0]['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        for issue in issues:
            created_at = datetime.datetime.strptime(issue['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            start_itter = int((created_at - start_date).total_seconds() /
                iteration_length)
            end_itter = None
            if (issue["closed_at"]):
                closed_at = datetime.datetime.strptime(issue['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
                time_since_closed = closed_at - start_date
                end_itter = int(time_since_closed.total_seconds() / iteration_length)

            if not end_itter:
                #20 years aught to be enough
                end_itter = 52
            label_name = None
            for label in issue["labels"]:
                if label['name'] in label_point_map.keys():
                    #incrament from creation date to closed date
                    # print("#", issue['number'] ,"issue: ",
                    # issue['title'], "started_at", issue["created_at"],
                    # " closed at ", issue["closed_at"], label['name'], end_itter)
                    label_name = label['name']
            #for every itter from start to end run this
            if label_name:
                for i in range(start_itter, end_itter):
                    if not i in data:
                        data[i] = 0
                    data[i] = data[i] + label_point_map[label_name]
                    #if issue is part of a
    return (start_date, data)

start_date, iters = generate_burngraph()
objects=[]
for key, value in iters.items():
    objects.append( {key: value})

print """
<!DOCTYPE html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title></title>
        <link rel='stylesheet' href='colorbrewer.css'/>
        <script type="text/javascript" src="colorbrewer.js"></script>
        <script type="text/javascript" src="jquery-ui-1.8.19.custom/js/jquery-1.7.1.min.js"></script>
        <script type="text/javascript" src="https://raw.github.com/mbostock/d3/master/d3.v2.min.js"></script>
        <script type="text/javascript" src="raphael-min.js"></script>
        <script type="text/javascript" src="chartz.js"></script>
        <style type="text/css">
            .barchart{
                height: 500px;
                width: 500px;
                border: solid black 1px;
            }
            .axis path,
            .axis line {
              fill: none;
              stroke: #000;
              shape-rendering: crispEdges;
            }
        </style>
        <script type="text/javascript">
            function attachEvents(objects){
                objects.forEach(function(b){
                    var origColor = b.attr('fill');
                    b.mouseover(function(){
                        b.animate({
                            fill: 'red',
                            stroke: 'black',
                            'stroke-width': 1
                        }, 100);
                    });
                    b.mouseout(function(){
                        b.animate({
                            fill: origColor,
                            'stroke': 'black',
                            'stroke-width': 1
                        }, 100);
                    });
                });
            }
            $(document).ready(function(){
                var linedata = %s;
                paper = cir.chartz.lineChart("#numLineChart", linedata, {'axis': true});
                attachEvents(paper.dots);
            });
        </script>
    </head>
    <body>
        <div id="numLineChart" class="barchart"></div>

    <ul>
""" % json.dumps(objects)
for week, points in iters.items():
        current = start_date + datetime.timedelta(seconds=week * iteration_length)
        print "    <li>iteration: %s (week of %s), hours of backlog: %s </li>" % (week, current.date(), points)
print """
    </ul>
    </body>
</html>"""
