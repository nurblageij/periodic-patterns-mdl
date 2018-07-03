import re, datetime
import pdb

MIN_OCC = 10

OUT_REP = "prepared"
IN_FILE = "all_log_applications_nonbin.txt"

users = {}
users_drop = set()
with open(IN_FILE) as fp:
    for li, line in enumerate(fp):
        tmp = re.match('(?P<user>[0-9]*_[FM])/(?P<file>log_[0-9\-]+.txt):.*"ProcessName":"(?P<process>[^"]*)",.*"Start":"(?P<start_time>[^"]*)",.*"End":"(?P<end_time>[^"]*)"', line)
        if tmp is not None:
            user = tmp.group("user")
            d = None
            if user not in users_drop:
                try:
                    d = (datetime.datetime.strptime(tmp.group("start_time"), '%m-%d-%Y %H:%M:%S'),
                         datetime.datetime.strptime(tmp.group("end_time"), '%m-%d-%Y %H:%M:%S'))
                except ValueError:
                    users_drop.add(user)
                    d = None

            if user not in users_drop and d is not None:
                if user not in users:
                    users[user] = {"ev": [], "counts": {}}
                    
                delta = (d[1]-d[0]).total_seconds()
                if delta < 60: ## last less than a minute
                    evs = [(d[0], "%s_I" % tmp.group("process"))]
                else:
                    evs = [(d[0], "%s_S" % tmp.group("process")), (d[1], "%s_E" % tmp.group("process"))]
                for (tt, ev) in evs:
                    users[user]["ev"].append((tt, ev))
                    users[user]["counts"][ev] = users[user]["counts"].get(ev, 0)+1

print "DROP", users_drop
for user, dt in users.items():
    if user not in users_drop:
        evs_tmp = [d for d in dt["ev"] if dt["counts"].get(d[1], 0) > MIN_OCC]
        if len(evs_tmp) > MIN_OCC:
            evs_tmp = sorted(evs_tmp)
            evs = sorted([(int((d[0]-evs_tmp[0][0]).total_seconds()/60), d[-1]) for d in evs_tmp])
            with open("%s/%s_ISE_data.dat" % (OUT_REP, user), "w") as fo:
                fo.write("### user=%s\tstart_time=%s\n" % (user, evs_tmp[0][0]))
                prev = None
                for pair in evs:
                    if pair != prev:
                        fo.write("%d\t%s\n" % pair)
                        prev = pair
                    

            with open("%s/%s_IS_data.dat" % (OUT_REP, user), "w") as fo:
                fo.write("### user=%s\tstart_time=%s\n" % (user, evs_tmp[0][0]))
                prev = None
                for tt in evs:
                    db = tt[-1].split("_")
                    if db[-1] in ["I", "S"]:
                        pair = (tt[0], "_".join(db[:-1]))
                        if pair != prev:
                            fo.write("%d\t%s\n" % pair)
                            prev = pair
