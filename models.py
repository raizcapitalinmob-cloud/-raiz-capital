from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre   = db.Column(db.String(128), default='')
    created  = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)
    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Propiedad(db.Model):
    __tablename__ = 'propiedades'
    id              = db.Column(db.Integer, primary_key=True)
    dir             = db.Column(db.String(256), nullable=False)
    zona            = db.Column(db.String(128), default='')
    emoji           = db.Column(db.String(8),   default='🏠')
    inquilino       = db.Column(db.String(128), default='')
    dni             = db.Column(db.String(32),  default='')
    tel             = db.Column(db.String(32),  default='')
    email           = db.Column(db.String(128), default='')
    alquiler        = db.Column(db.Float,       default=0)
    deposito        = db.Column(db.Float,       default=0)
    inicio          = db.Column(db.String(12),  default='')
    fin             = db.Column(db.String(12),  default='')
    estado          = db.Column(db.String(32),  default='Activo')
    # Actualización
    indice_actualizacion = db.Column(db.String(8),  default='ICL')   # ICL o IPC
    meses_actualizacion  = db.Column(db.Integer,    default=3)        # 3, 4 o 6
    ultima_actualizacion = db.Column(db.String(12), default='')       # fecha última actualización
    created         = db.Column(db.DateTime, default=datetime.utcnow)
    pagos           = db.relationship('Pago',     backref='propiedad', lazy=True, cascade='all,delete')
    impuestos       = db.relationship('Impuesto', backref='propiedad', lazy=True, cascade='all,delete')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Pago(db.Model):
    __tablename__ = 'pagos'
    id           = db.Column(db.Integer, primary_key=True)
    propiedad_id = db.Column(db.Integer, db.ForeignKey('propiedades.id'), nullable=False)
    periodo      = db.Column(db.String(16), default='')
    estado       = db.Column(db.String(32), default='Pendiente')
    fecha_pago   = db.Column(db.String(12), default='')
    monto        = db.Column(db.Float,      default=0)
    descuento    = db.Column(db.Float,      default=0)    # descuento por gastos
    descripcion  = db.Column(db.String(512), default='')  # detalle del gasto/descuento
    num_recibo   = db.Column(db.Integer,    default=0)
    created      = db.Column(db.DateTime,   default=datetime.utcnow)

    def to_dict(self):
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        d['prop_dir']      = self.propiedad.dir      if self.propiedad else ''
        d['prop_inquilino']= self.propiedad.inquilino if self.propiedad else ''
        d['prop_dni']      = self.propiedad.dni       if self.propiedad else ''
        d['prop_alquiler'] = self.propiedad.alquiler  if self.propiedad else 0
        return d

class Impuesto(db.Model):
    __tablename__ = 'impuestos'
    id           = db.Column(db.Integer, primary_key=True)
    propiedad_id = db.Column(db.Integer, db.ForeignKey('propiedades.id'), nullable=False)
    tipo         = db.Column(db.String(64),  default='')
    periodo      = db.Column(db.String(16),  default='')
    monto        = db.Column(db.Float,       default=0)
    vto          = db.Column(db.String(12),  default='')
    estado       = db.Column(db.String(32),  default='Pendiente')
    created      = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        d['prop_dir'] = self.propiedad.dir if self.propiedad else ''
        return d

class Config(db.Model):
    __tablename__ = 'config'
    id    = db.Column(db.Integer, primary_key=True)
    key   = db.Column(db.String(64), unique=True)
    value = db.Column(db.String(256))
