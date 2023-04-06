from sqlalchemy import Table, Column, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.db.base_class import Base


StatusPageMonitor = Table('statuspage_monitor', Base.metadata,
    Column('monitor_id', Integer, ForeignKey('monitor.id')),
    Column('statuspage_id', Integer, ForeignKey('statuspage.id'))
)


class StatusPage(Base):
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String)
    subdomain = Column(String, index=True, unique=True)
    company_website = Column(String)

    owner_id = Column(Integer, ForeignKey("user.id"))
    owner = relationship("User", back_populates="statuspages")
    monitors = relationship(
        "Monitor",
        secondary=StatusPageMonitor,
    )

    @hybrid_property
    def monitor_ids(self):
        return [m.id for m in self.monitors]

    @hybrid_property
    def up(self):
        return all([m.up for m in self.monitors])
