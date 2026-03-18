from pydantic import BaseModel, Field


class Connection(BaseModel):
    zone_a: str
    zone_b: str
    max_link_capacity: int = Field(default=1)

    def other_end(self, zone_name: str):
        try:
            if zone_name == self.zone_a:
                return (self.zone_b)
            elif zone_name == self.zone_b:
                return (self.zone_a)
        except ValueError:
            print("Error")
