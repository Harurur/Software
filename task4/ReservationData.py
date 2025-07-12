from datetime import date
from typing import Tuple, List

class ReservationData
  def __init__(self, reservation_date: date, num_rooms: int, check_in_date: date, check_out_date: date):
        self.reservation_date = reservation_date
        self.room_number = room_number
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
 
  def get_check_date(self)-> Tuple[datatime.date, datatime.data]:
    return self.check_in_date, self.check_out_date
    
  def get_room_number(self)->List[str]:
    return self.room_number
    
  def make_reservation_data(self)->dict:
    return {
      "reservation_id": self.reservation_id,
      "reservation_date": self.reservation_date.isoformat(),
      "num_rooms": self.num_rooms,
      "check_in_date": self.check_in_date.isoformat(),
      "check_out_date": self.check_out_date.isoformat(),
      "room_numbers": self.room_numbers
    }

  def __str__(self):
      return (f"予約ID: {self.reservation_id}, 予約日: {self.reservation_date}, "
              f"部屋数: {self.num_rooms}, チェックイン: {self.check_in_date}, "
              f"チェックアウト: {self.check_out_date}, 部屋番号: {self.room_numbers}")
    
  
