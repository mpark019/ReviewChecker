from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint, Date
from database import Base
from sqlalchemy.orm import relationship

# class Reviews(Base):
#     __tablename__ = 'reviews'

#     id = Column(Integer, primary_key=True, index=True)
#     review_text = Column(String, index=True)

# class Names(Base):
#     __tablename__ = 'names'

#     id = Column(Integer, primary_key=True, index=True)
#     name_text = Column(String, index=True)
#     review_id = Column(Integer, ForeignKey("reviews.id"))
#     # text = Column(String, ForeignKey("reviews.review_text"))

class Employees(Base):
    __tablename__ = 'employee'

    id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String, index=True)
    counts = relationship("Counts")
    
class Counts(Base):
    __tablename__ = 'count'
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uix_emp_date"),)

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    count = Column(Integer, nullable=False, default=0)
    
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    employee = relationship("Employees", back_populates="counts")

