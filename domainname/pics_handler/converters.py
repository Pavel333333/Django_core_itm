class FourDigitYearConverter:
    regex: str = "[0-9]{4}"

    def to_python(self, value: str) -> int:
        return int(value)

    def to_url(self, value: int) -> str:
        return "%04d" % value