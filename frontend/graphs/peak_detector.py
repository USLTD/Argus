class PeakDetector:

    @staticmethod
    def peak(values):

        if not values:
            return 0

        return max(values)