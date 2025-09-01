import yaml 
import re
from datetime import datetime


def formatDate(date):

    # Parse the string into a datetime object
    dt = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z")

    # Format back without time/offset
    formattedDate = dt.strftime("%a, %d %b %Y")
    return formattedDate



# Loads requested yaml file located at file_path
def load_config(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
    
def find_text(query, text, regex):
        split_text = text.split('\n')
        split_query =  query.split()
        num_query_words = len(split_query)
        word = ''
        for line in split_text:
            if query in line:
                print(line)
                
                split_line = line.split()
                for word in split_line:
                    if re.search(regex, word):
                        break
                break
        return word

def find_distance_duration(query, text):
     split_text = text.split('\n')
     distance = ""
     duration = ""
     for line in split_text:
          if query in line:
               distDurSplit = line.split('|')
               distance = distDurSplit[0]
               duration = distDurSplit[1][:-1]
               break
     return distance, duration


def pickUpDropOffInfo(billEmailText):
    WS = r"(?:\s|\u00A0|\u202F)"

    pattern = re.compile(
        rf'^\s*'
        rf'(?P<street_number>\d{{1,6}})\s+(?P<street>[^,]+?),\s*'
        rf'(?P<city>[A-Za-z][A-Za-z.\-\s\'’]+),\s*'  # allow apostrophes/curly apostrophes
        rf'(?P<province>AB|BC|MB|NB|NL|NS|NT|NU|ON|PE|QC|SK|YT)\s+'
        rf'(?P<postal>[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTVWXYZ]{WS}?\d[ABCEGHJ-NPRSTVWXYZ]\d)'
        rf'\s*,\s*CA\s*$',
        re.IGNORECASE
    )

    addressDict = {
        "fromAddress" : {}, 
        "toAddress" : {}
    }

    timeDict = {
        "fromTime" : "", 
        "toTime" : ""
    }
    splitBillText = billEmailText.split('\n')
    for index,line in enumerate(splitBillText):
        addressPatternMatch = pattern.match(line)
        if addressPatternMatch:
            print(True)
            if addressDict['fromAddress'] == {}:
                addressDict['fromAddress'] = addressPatternMatch.groupdict()
                timeDict['fromTime'] = splitBillText[index - 1]
            elif addressDict['toAddress'] == {}:
                addressDict['toAddress'] = addressPatternMatch.groupdict()
                timeDict['toTime'] = splitBillText[index - 1]
    return addressDict['fromAddress'], addressDict['toAddress'], timeDict['fromTime'][:-1], timeDict['toTime'][:-1]
            

                
def compressText(text, compressor): 
        return compressor.compress(text)         

