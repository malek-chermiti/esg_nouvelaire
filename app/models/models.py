from typing import Optional
import datetime
import decimal

from sqlalchemy import Date, Double, ForeignKeyConstraint, Index, Integer, String, TIMESTAMP, Text, text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class AviationLicense(Base):
    __tablename__ = 'aviation_license'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    license_type: Mapped[str] = mapped_column(String(50), nullable=False)
    authority: Mapped[str] = mapped_column(String(50), nullable=False)
    issue_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    period_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    license_number: Mapped[Optional[str]] = mapped_column(String(50))
    renewal_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(15), server_default=text("'ACTIVE'"))
    route_concerned: Mapped[Optional[str]] = mapped_column(String(15))
    aircraft_concerned: Mapped[Optional[str]] = mapped_column(String(20))
    cost_tnd: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))


class Co2Emission(Base):
    __tablename__ = 'co2_emission'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route: Mapped[str] = mapped_column(String(15), nullable=False)
    co2_kg: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True), nullable=False)
    period_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    distance_km: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    nb_passengers: Mapped[Optional[int]] = mapped_column(Integer)
    aircraft_type: Mapped[Optional[str]] = mapped_column(String(20))


class Employee(Base):
    __tablename__ = 'employee'
    __table_args__ = (
        Index('employee_code', 'employee_code', unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)
    hire_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    department: Mapped[str] = mapped_column(String(30), nullable=False)
    exit_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    job_title: Mapped[Optional[str]] = mapped_column(String(50))
    contract_type: Mapped[Optional[str]] = mapped_column(String(10), server_default=text("'CDI'"))
    site: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'1'"))

    training: Mapped[list['Training']] = relationship('Training', back_populates='employee')
    work_accident: Mapped[list['WorkAccident']] = relationship('WorkAccident', back_populates='employee')


class FuelSurcharge(Base):
    __tablename__ = 'fuel_surcharge'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount_tnd: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True), nullable=False)
    period_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    route: Mapped[Optional[str]] = mapped_column(String(15))


class PaymentTracking(Base):
    __tablename__ = 'payment_tracking'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_tnd: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True), nullable=False)
    payment_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    period_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_traceable: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'1'"))


class Pillar(Base):
    __tablename__ = 'pillar'
    __table_args__ = (
        Index('code', 'code', unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(1), nullable=False)
    weight: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True), server_default=text("'0.33'"))

    kpi: Mapped[list['Kpi']] = relationship('Kpi', back_populates='pillar')


class TaxObligation(Base):
    __tablename__ = 'tax_obligation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tax_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount_tnd: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True), nullable=False)
    period_start: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    period_end: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String(15), server_default=text("'PENDING'"))
    authority: Mapped[Optional[str]] = mapped_column(String(30))
    reference_num: Mapped[Optional[str]] = mapped_column(String(50))


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('email', 'email', unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'VIEWER'"))
    is_active: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'1'"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))


class WasteManagement(Base):
    __tablename__ = 'waste_management'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site: Mapped[str] = mapped_column(String(50), nullable=False)
    period_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    waste_type: Mapped[str] = mapped_column(String(20), nullable=False)
    weight_kg: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True), nullable=False)
    is_recycled: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'0'"))
    disposal_method: Mapped[Optional[str]] = mapped_column(String(30))


class Kpi(Base):
    __tablename__ = 'kpi'
    __table_args__ = (
        ForeignKeyConstraint(['pillar_id'], ['pillar.id'], name='kpi_ibfk_1'),
        Index('code', 'code', unique=True),
        Index('pillar_id', 'pillar_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    better_direction: Mapped[str] = mapped_column(String(10), nullable=False)
    pillar_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    weight: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True), server_default=text("'0.33'"))

    pillar: Mapped['Pillar'] = relationship('Pillar', back_populates='kpi')
    anomaly: Mapped[list['Anomaly']] = relationship('Anomaly', back_populates='kpi')


class Training(Base):
    __tablename__ = 'training'
    __table_args__ = (
        ForeignKeyConstraint(['employee_id'], ['employee.id'], name='training_ibfk_1'),
        Index('employee_id', 'employee_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    training_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    training_type: Mapped[str] = mapped_column(String(20), nullable=False)
    hours: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True), nullable=False)
    cost_tnd: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    provider: Mapped[Optional[str]] = mapped_column(String(20), server_default=text("'INTERNAL'"))
    description: Mapped[Optional[str]] = mapped_column(String(200))

    employee: Mapped['Employee'] = relationship('Employee', back_populates='training')


class WorkAccident(Base):
    __tablename__ = 'work_accident'
    __table_args__ = (
        ForeignKeyConstraint(['employee_id'], ['employee.id'], name='work_accident_ibfk_1'),
        Index('employee_id', 'employee_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    accident_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    hours_lost: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True), server_default=text("'0'"))
    department: Mapped[Optional[str]] = mapped_column(String(30))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_lost_time: Mapped[Optional[int]] = mapped_column(TINYINT(1), server_default=text("'0'"))

    employee: Mapped['Employee'] = relationship('Employee', back_populates='work_accident')


class Anomaly(Base):
    __tablename__ = 'anomaly'
    __table_args__ = (
        ForeignKeyConstraint(['kpi_id'], ['kpi.id'], name='anomaly_ibfk_1'),
        Index('kpi_id', 'kpi_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kpi_id: Mapped[int] = mapped_column(Integer, nullable=False)
    detected_value: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    expected_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    z_score: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    status: Mapped[Optional[str]] = mapped_column(String(15), server_default=text("'NEW'"))
    date_detected: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    description: Mapped[Optional[str]] = mapped_column(Text)

    kpi: Mapped['Kpi'] = relationship('Kpi', back_populates='anomaly')
    recommendation: Mapped[list['Recommendation']] = relationship('Recommendation', back_populates='anomaly')


class Recommendation(Base):
    __tablename__ = 'recommendation'
    __table_args__ = (
        ForeignKeyConstraint(['anomaly_id'], ['anomaly.id'], name='recommendation_ibfk_1'),
        Index('anomaly_id', 'anomaly_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anomaly_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    impact_estimated: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[Optional[str]] = mapped_column(String(15), server_default=text("'PENDING'"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    anomaly: Mapped['Anomaly'] = relationship('Anomaly', back_populates='recommendation')
