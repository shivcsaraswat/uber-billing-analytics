import pandas as pd
class DFRecords:
    def __init__(self, records):
        self.recordDF = pd.DataFrame(records)
    
    def getRecordDF(self):
        return self.recordDF
    

            
