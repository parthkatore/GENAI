from dataclasses import dataclass

@dataclass
class Record:
    function_name: str
    category: str
    syntax: str
    returns: str
    common_gotcha: str
    source_url: str