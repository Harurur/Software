import datetime

class ReservationData:
  def __init__(self, reservation_date: datetime.date, room_number: int, check_in_date: datetime.date, check_out_date: datetime.date):
        self.reservation_date = reservation_date
        self.room_number = room_number
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
 
  def get_check_in_date(self):
      return self.check_in_date
  
  def get_check_out_data(self):
      return self.check_out_date
      
  def get_room_number(self):
      return self.room_number
  
  ##def make_reservation_data(self):
