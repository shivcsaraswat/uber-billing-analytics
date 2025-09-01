from utils.utils import *
import copy

mailParser = load_config('./uberMailParser.yaml')

class TripParser():
    def __init__(self, eid ,date, emailText, compressionAlgo):

        self.trip = {
        'eid': eid,
        'date': formatDate(date),
        'emailText': compressText(emailText.encode('utf-8'), compressionAlgo) if isinstance(emailText, str) else emailText,
        'compressorName': compressionAlgo.__name__,
        'total': find_text(mailParser['UberBillAttr']['Total'], emailText, mailParser['UberBillAttr']['Regex']['PriceRegex']),
        'tripFare': find_text(mailParser['UberBillAttr']['Trip_Fare'], emailText, mailParser['UberBillAttr']['Regex']['PriceRegex']),
        'subtotal': find_text(mailParser['UberBillAttr']['Subtotal'], emailText, mailParser['UberBillAttr']['Regex']['PriceRegex']),
        'insurance': find_text(mailParser['UberBillAttr']['Insurance'], emailText, mailParser['UberBillAttr']['Regex']['PriceRegex']),
        'HST': find_text(mailParser['UberBillAttr']['HST'], emailText, mailParser['UberBillAttr']['Regex']['PriceRegex']),
        'TNC': find_text(mailParser['UberBillAttr']['tnc_recovery_fees'], emailText, mailParser['UberBillAttr']['Regex']['PriceRegex']),
        'driver': find_text(mailParser['UberBillAttr']['driver'], emailText, mailParser['UberBillAttr']['Regex']['DriverRegex']),
        'driverRating': find_text(mailParser['UberBillAttr']['driverRating'], emailText, mailParser['UberBillAttr']['Regex']['RatingRegex'])
        }
        
        distance, duration = find_distance_duration(mailParser['UberBillAttr']['distance'], emailText)
        self.trip['distance'] = distance
        self.trip['duration'] = duration
        
        pickupLocation, dropOffLocation, pickUpTime, dropTime = pickUpDropOffInfo(emailText)
        self.trip['pickupLocation'] = pickupLocation
        self.trip['dropOffLocation'] = dropOffLocation
        self.trip['pickUpTime'] = pickUpTime
        self.trip['dropTime'] = dropTime

    def __str__(self):
        return copy.deepcopy(self.trip)
       
       
    
    

    
    

    
