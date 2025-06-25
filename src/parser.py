def tokenizeHands(ranges):
    """Parse a line from the converted format into hand combinations with weights"""
    hands = []
    lines = ranges.strip().split('\n')[1:]  # Skip header
    for line in lines:
        if line.startswith('----'): continue  # Skip separator
        parts = line.split()
        if len(parts) >= 4:  # Hand Call% Fold% Total%
            hand = parts[0]
            call_pct = float(parts[1])  # Prima colonna numerica = Call%
            fold_pct = float(parts[2])  # Seconda colonna numerica = Fold%
            
            # Solo le mani con call% > 0 vengono aggiunte
            if call_pct > 0:
                hands.append((hand, call_pct))
    return hands

def parseLine(filename):
    with open(filename) as f:
        content = f.read()
    
    ret = {}
    # Le mani con call% > 0 vanno nel call (prima colonna numerica)
    ret["call"] = []
    # Non ci sono azioni "raise" nei file convertiti, solo Call e Fold
    ret["raise"] = []
    
    lines = content.strip().split('\n')[1:]  # Skip header
    for line in lines:
        if line.startswith('----'): continue
        parts = line.split()
        if len(parts) >= 4:
            hand = parts[0]
            call_pct = float(parts[1])  # Prima colonna numerica = Call%
            fold_pct = float(parts[2])  # Seconda colonna numerica = Fold%
            
            # Solo le mani con call% > 0 vanno nel call
            if call_pct > 0:
                ret["call"].append((hand, call_pct))
    
    return ret

def parseLines(filename):
    try:
        ret = parseLine(filename)
        return ret, True
    except Exception as e:
        return str(e), False

def parseDepends(line):
    line = line[1].split(" ")
    arr = []
    for i in range(len(line)):
        if line[i] != "":
            arr.append(line[i])
    return arr
            
def parseDictionaryToFile(filename, dictionary, dependencyFile=None):
    try:
        raiseArr = dictionary["raise"]
        callArr = dictionary["call"]
        f = open(filename, 'w')
        curWeight = None
        for idx, item in enumerate(raiseArr):
            itemWeight = item[1]
            if curWeight is None or curWeight != itemWeight:
                curWeight = itemWeight
                f.write("W" + str(curWeight) + ": ")
            if idx != len(raiseArr)-1:
                f.write(item[0] + ", ")
            else:
                f.write(item[0] + "; ")
            # no comma for last value
        curWeight = None
        for idx, item in enumerate(callArr):
            itemWeight = item[1]
            if curWeight is None or curWeight != itemWeight:
                curWeight = itemWeight
                f.write("W" + str(curWeight) + ": ")
            if idx != len(callArr)-1:
                f.write(item[0] + ", ")
            else:
                f.write(item[0])
        if dependencyFile is not None:
            res, success = parseLines(dependencyFile)
            if success:
                # Build dependency array
                depArr = []
                for key in res["raise"]:
                    depArr.append(key[0]) 
                if res["call"] is not None:
                    for key in res["call"]:
                        if key not in depArr:
                            depArr.append(key[0])
                f.write("\nDepends: ")
                for key in depArr:
                    f.write(key + " ") 
            else:
                return False
        f.close()
        return True
    except:
        return False
