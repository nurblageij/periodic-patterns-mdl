import numpy
import datetime, re, csv

import pdb

FOLDER="./"
FILENAME_DATA = "data.csv"
FILENAME_MAPIDS = "map_ids.txt"

FILENAME_OUT = FOLDER+"data_lagg200NL-new.txt"
CODES_OUT = FOLDER+"event_codes_out-new.txt"

time_scale = 60

def del_instant(events):
    ##### DELETE TIME 0
    i = 0
    while i < len(events):
        if (events[i][0] == events[i][1]):
            events.pop(i)
        else:
            i+=1

def merge_samesucc(events):
    ##### MERGE SUCCESSIVE SAME
    i = 0
    while i < len(events)-1:
        if (events[i][2] == events[i+1][2]) and (events[i][0] == events[i+1][1]):
            events[i][0] = events[i+1][0]
            events.pop(i+1)
        else:
            i+=1
            
def print_out(events, filename):
    ##### PRINT OUT
    origin = events[-1][0]
    with open(filename, "w") as fo:
        while len(events) > 1:
            ev = events.pop()
            fo.write("%d %d %d %d %s %s\n" % (ev[2], (ev[0]-origin).total_seconds() / time_scale, (ev[1]-origin).total_seconds() / time_scale, (ev[1]-ev[0]).total_seconds() / time_scale, ev[0], ev[3]))

            
def read_mapp(filename):
    mapp = {}
    with open(filename) as fp:
        for line in fp:
            parts = line.strip().split()
            mapp[parts[2]] = (int(parts[0]), int(parts[1]), parts[3])
    return mapp
            
def read_data(filename, mapp): # FOLDER+FILENAME_DATA
    missing_act = set()
    events = []
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            if len(row["End timestamp"]) > 0 and row["Record category type"] == "activity":
                t0 = datetime.datetime.strptime(row["Timestamp"], "%B %d, %Y %H:%M")
                t1 = datetime.datetime.strptime(row["End timestamp"], "%B %d, %Y %H:%M")
                activity = re.sub(" ", "", row["Record category"])
                if activity in mapp:
                    events.append([t0, t1, mapp[activity][1], mapp[activity][2], mapp[activity][0], activity])
                else:
                    missing_act.add(activity)
            # print row["Timestamp"], "->", tt , "---", row["Record category"], row["Record category type"]
    print missing_act
    return events

def aggregate_rare(events, mapp, thres=100, lego=False):
    ids_to_names = dict([(v[1],v[2]) for (k,v) in mapp.items()])
    names_to_ids = dict([(v[2],v[1]) for (k,v) in mapp.items()])
    nks = names_to_ids.keys()
    for n in nks:
        pos = [2]
        if re.search("LEGO", n) and lego:
            pos.append(3)
        for p in pos:
            nnk = "-".join(n.split("-")[:p])
            if nnk not in names_to_ids:
                names_to_ids[nnk] = int(("%d" % names_to_ids[n])[:p])
                ids_to_names[names_to_ids[nnk]] = nnk
    dt = numpy.array([e[2] for e in events])
    occs = dict([(v, numpy.where(dt==v)[0]) for v in numpy.unique(dt)])

    map_agg = {}
    for (k,v) in occs.items():
        if thres is None or v.shape[0] < thres:
            if re.search("LEGO", ids_to_names[k]) and lego:
                map_agg[k] = names_to_ids["-".join(ids_to_names[k].split("-")[:3])]
            else:
                map_agg[k] = names_to_ids["-".join(ids_to_names[k].split("-")[:2])] 

    for i in range(len(events)):
        events[i][2] = map_agg.get(events[i][2], events[i][2])
    dt_agg = numpy.array([e[2] for e in events])
    occs_agg = dict([(v, numpy.where(dt_agg==v)[0]) for v in numpy.unique(dt_agg)])
    with open(CODES_OUT, "w") as ff:
        ff.write("\n".join(["%s\t%s" % (v, k) for (k,v) in names_to_ids.items()]))

    print "--- Aggregated %d -> %d" % (len(occs), len(occs_agg))
    # print len(occs), sorted([(x[1].shape[0], ids_to_names[x[0]]) for x in occs.items()])
    # print len(occs_agg), sorted([(x[1].shape[0], ids_to_names[x[0]]) for x in occs_agg.items()])
    return events
    
mapp = read_mapp(FOLDER+FILENAME_MAPIDS)
events = read_data(FOLDER+FILENAME_DATA, mapp)

del_instant(events)
aggregate_rare(events, mapp, thres=200, lego=False)

merge_samesucc(events)


print "Printing out %d events to %s" % (len(events), FILENAME_OUT)
print_out(events, FILENAME_OUT)
