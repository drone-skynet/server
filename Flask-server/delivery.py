class Delivery:
  def __init__(self, content, origin, destination):
    self.content = content
    self.origin = origin
    self.destination = destination
    self.is_reserved= False

  def __repr__(self) :
    return f"Delivery : {{content : {self.content}, origin : {self.origin}, destination : {self.destination}, is_reserved : {self.is_reserved}}}"