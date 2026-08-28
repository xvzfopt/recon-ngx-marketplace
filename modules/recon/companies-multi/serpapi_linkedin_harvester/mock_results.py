# =====================================================================================
# MockResults Class (Test Only)
# =====================================================================================
class MockResults(dict):
    '''
    SerpApi Mock Results class. Used only for Unittest purposes
    '''

    def __init__(self, data):
        '''
        Constructor

        :param data: The SerpApi results data
        :type: dict
        '''
        super().__init__(data)

    def as_dict(self):
        '''
        Returns the SerpApi Mock Results data

        :returns: SerpApi Mock Results data
        :rtype: dict
        '''
        return self