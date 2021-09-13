from pydantic import BaseModel
from typing import Dict, List, Union


class ScrapedData(BaseModel):
    id: str
    employers: Union[List[Dict], Dict]
    created_at: str
    full_name: str
    picture_url: str
    address: dict
