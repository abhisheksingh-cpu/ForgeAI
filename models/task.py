from pydantic import BaseModel

class EngineeringTask(BaseModel):
    title : str
    description : str
    language : str
    framework : str
    database : str 
    authentication : str
    