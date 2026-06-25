import os, json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Propiedad, Pago, Impuesto, Config
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'raiz-capital-2026-secret-cambiar')
# Railway PostgreSQL fix: replace postgres:// with postgresql://
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///raiz_capital.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ── Init DB ──────────────────────────────────────
def init_db():
    db.create_all()
    # Add new columns if they don't exist (for existing DBs)
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE propiedades ADD COLUMN indice_actualizacion VARCHAR(8) DEFAULT 'ICL'"))
            conn.commit()
    except: pass
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE propiedades ADD COLUMN meses_actualizacion INTEGER DEFAULT 3"))
            conn.commit()
    except: pass
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE propiedades ADD COLUMN ultima_actualizacion VARCHAR(12) DEFAULT ''"))
            conn.commit()
    except: pass
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE pagos ADD COLUMN descuento FLOAT DEFAULT 0"))
            conn.commit()
    except: pass
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE pagos ADD COLUMN descripcion VARCHAR(512) DEFAULT ''"))
            conn.commit()
    except: pass

    if not User.query.filter_by(username='tomas').first():
        u = User(username='tomas', nombre='Tomás Linares')
        u.set_password('raiz2026')
        db.session.add(u)
    if not Config.query.filter_by(key='receipt_num').first():
        db.session.add(Config(key='receipt_num', value='64'))
    if not Propiedad.query.first():
        props = [
            Propiedad(dir='Caleta de los Loros 123', zona='Balneario El Cóndor', emoji='🏖️',
                      inquilino='García, Juan', dni='32.456.789', tel='2920-415233',
                      email='jgarcia@mail.com', alquiler=85000, deposito=255000,
                      inicio='2024-03-01', fin='2025-03-01', estado='Activo',
                      indice_actualizacion='ICL', meses_actualizacion=3,
                      ultima_actualizacion='2024-03-01'),
            Propiedad(dir='Las Grutas, Lote 42', zona='Las Grutas', emoji='🌊',
                      inquilino='López, María', dni='28.123.456', tel='2920-556789',
                      email='mlopez@mail.com', alquiler=72000, deposito=216000,
                      inicio='2024-06-01', fin='2025-06-01', estado='Activo',
                      indice_actualizacion='IPC', meses_actualizacion=6,
                      ultima_actualizacion='2024-06-01'),
            Propiedad(dir='Balneario El Cóndor, Casa 7', zona='Balneario El Cóndor', emoji='🏡',
                      inquilino='Pérez, Carlos', dni='35.789.012', tel='2920-334455',
                      email='cperez@mail.com', alquiler=65000, deposito=195000,
                      inicio='2023-12-01', fin='2024-12-01', estado='En Renovación',
                      indice_actualizacion='ICL', meses_actualizacion=4,
                      ultima_actualizacion='2023-12-01'),
            Propiedad(dir='Las Carmelitas, Dpto 2', zona='Las Carmelitas', emoji='🏠',
                      inquilino='Rodríguez, Ana', dni='30.654.321', tel='2920-778899',
                      email='arodriguez@mail.com', alquiler=58000, deposito=174000,
                      inicio='2024-09-01', fin='2025-09-01', estado='Activo',
                      indice_actualizacion='IPC', meses_actualizacion=3,
                      ultima_actualizacion='2024-09-01'),
        ]
        for p in props: db.session.add(p)
        db.session.flush()
        imps = [
            Impuesto(propiedad_id=props[0].id, tipo='ABL', periodo='Jun-2026', monto=12500, vto='2026-06-10', estado='Pagado'),
            Impuesto(propiedad_id=props[0].id, tipo='Inmobiliario Prov.', periodo='Jun-2026', monto=8900, vto='2026-06-20', estado='Pendiente'),
            Impuesto(propiedad_id=props[1].id, tipo='ABL', periodo='Jun-2026', monto=9800, vto='2026-06-10', estado='Pagado'),
            Impuesto(propiedad_id=props[2].id, tipo='Expensas', periodo='Jun-2026', monto=15000, vto='2026-06-15', estado='Pendiente'),
            Impuesto(propiedad_id=props[3].id, tipo='Luz', periodo='Jun-2026', monto=6200, vto='2026-06-12', estado='Pagado'),
        ]
        for i in imps: db.session.add(i)
    db.session.commit()

# ── Helpers ──────────────────────────────────────
def dias_para_actualizar(prop):
    """Returns days until next update is due. Negative = overdue."""
    if not prop.ultima_actualizacion:
        return None
    try:
        ultima = datetime.strptime(prop.ultima_actualizacion, '%Y-%m-%d').date()
        proxima = ultima + relativedelta(months=prop.meses_actualizacion or 3)
        return (proxima - date.today()).days
    except:
        return None

# ── Auth ─────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username','')).first()
        if u and u.check_password(request.form.get('password','')):
            login_user(u, remember=True)
            return redirect(url_for('index'))
        return render_template('login.html', error='Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/cambiar-password', methods=['POST'])
@login_required
def cambiar_password():
    data = request.get_json()
    if not current_user.check_password(data.get('actual','')):
        return jsonify({'ok': False, 'msg': 'Contraseña actual incorrecta'})
    nueva = data.get('nueva','')
    if len(nueva) < 6:
        return jsonify({'ok': False, 'msg': 'Mínimo 6 caracteres'})
    current_user.set_password(nueva)
    db.session.commit()
    return jsonify({'ok': True})

# ── Main ──────────────────────────────────────────
@app.route('/')
@login_required
def index():
    return render_template('app.html', usuario=current_user.nombre or current_user.username)

# ── API: Propiedades ──────────────────────────────
@app.route('/api/propiedades', methods=['GET'])
@login_required
def get_props():
    result = []
    for p in Propiedad.query.order_by(Propiedad.id).all():
        d = p.to_dict()
        d['dias_actualizacion'] = dias_para_actualizar(p)
        result.append(d)
    return jsonify(result)

@app.route('/api/propiedades', methods=['POST'])
@login_required
def add_prop():
    data = request.get_json()
    cols = Propiedad.__table__.columns.keys()
    p = Propiedad(**{k: data[k] for k in data if k in cols})
    if not p.ultima_actualizacion:
        p.ultima_actualizacion = p.inicio or date.today().isoformat()
    db.session.add(p)
    db.session.commit()
    d = p.to_dict()
    d['dias_actualizacion'] = dias_para_actualizar(p)
    return jsonify(d), 201

@app.route('/api/propiedades/<int:pid>', methods=['PUT'])
@login_required
def update_prop(pid):
    p = db.session.get(Propiedad, pid)
    if not p: return jsonify({'error':'not found'}), 404
    data = request.get_json()
    cols = Propiedad.__table__.columns.keys()
    for k, v in data.items():
        if k in cols and k != 'id':
            setattr(p, k, v)
    db.session.commit()
    d = p.to_dict()
    d['dias_actualizacion'] = dias_para_actualizar(p)
    return jsonify(d)

@app.route('/api/propiedades/<int:pid>', methods=['DELETE'])
@login_required
def delete_prop(pid):
    p = db.session.get(Propiedad, pid)
    if not p: return jsonify({'error':'not found'}), 404
    db.session.delete(p); db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/propiedades/<int:pid>/actualizar-precio', methods=['POST'])
@login_required
def actualizar_precio(pid):
    """Registra la actualización de precio y resetea el contador"""
    p = db.session.get(Propiedad, pid)
    if not p: return jsonify({'error':'not found'}), 404
    data = request.get_json()
    p.alquiler = data.get('nuevo_precio', p.alquiler)
    p.ultima_actualizacion = date.today().isoformat()
    db.session.commit()
    d = p.to_dict()
    d['dias_actualizacion'] = dias_para_actualizar(p)
    return jsonify(d)

# ── API: Pagos ────────────────────────────────────
@app.route('/api/pagos/periodo/<string:periodo>', methods=['GET'])
@login_required
def pagos_periodo(periodo):
    props = Propiedad.query.order_by(Propiedad.id).all()
    result = []
    for prop in props:
        pago = Pago.query.filter_by(propiedad_id=prop.id, periodo=periodo).first()
        result.append({
            'propiedad': {**prop.to_dict(), 'dias_actualizacion': dias_para_actualizar(prop)},
            'pago': pago.to_dict() if pago else None
        })
    return jsonify(result)

@app.route('/api/pagos/0/toggle', methods=['POST'])
@login_required
def toggle_pago():
    data = request.get_json()
    prop_id  = data['propiedad_id']
    periodo  = data['periodo']
    desc     = data.get('descripcion', '')
    descuento = float(data.get('descuento', 0) or 0)

    prop = db.session.get(Propiedad, prop_id)
    if not prop: return jsonify({'error':'not found'}), 404

    p = Pago.query.filter_by(propiedad_id=prop_id, periodo=periodo).first()
    if not p:
        p = Pago(propiedad_id=prop_id, periodo=periodo, monto=prop.alquiler)
        db.session.add(p)

    if p.estado == 'Pagado':
        p.estado = 'Pendiente'; p.fecha_pago = ''; p.num_recibo = 0
        p.descripcion = ''; p.descuento = 0
    else:
        p.estado = 'Pagado'
        p.fecha_pago = date.today().isoformat()
        p.monto = prop.alquiler  # siempre guardar el alquiler actual
        p.descripcion = desc
        p.descuento = descuento
        cfg = Config.query.filter_by(key='receipt_num').first()
        n = int(cfg.value) + 1
        cfg.value = str(n)
        p.num_recibo = n
    db.session.commit()
    return jsonify(p.to_dict())

@app.route('/api/pagos', methods=['GET'])
@login_required
def get_pagos():
    periodo = request.args.get('periodo','')
    q = Pago.query
    if periodo: q = q.filter_by(periodo=periodo)
    return jsonify([p.to_dict() for p in q.order_by(Pago.propiedad_id).all()])

# ── API: Impuestos ────────────────────────────────
@app.route('/api/impuestos', methods=['GET'])
@login_required
def get_impuestos():
    return jsonify([i.to_dict() for i in Impuesto.query.order_by(Impuesto.propiedad_id, Impuesto.vto).all()])

@app.route('/api/impuestos', methods=['POST'])
@login_required
def add_impuesto():
    data = request.get_json()
    cols = Impuesto.__table__.columns.keys()
    i = Impuesto(**{k: data[k] for k in data if k in cols})
    db.session.add(i); db.session.commit()
    return jsonify(i.to_dict()), 201

@app.route('/api/impuestos/<int:iid>/toggle', methods=['POST'])
@login_required
def toggle_impuesto(iid):
    i = db.session.get(Impuesto, iid)
    if not i: return jsonify({'error':'not found'}), 404
    i.estado = 'Pendiente' if i.estado == 'Pagado' else 'Pagado'
    db.session.commit()
    return jsonify(i.to_dict())

@app.route('/api/impuestos/<int:iid>', methods=['DELETE'])
@login_required
def delete_impuesto(iid):
    i = db.session.get(Impuesto, iid)
    if not i: return jsonify({'error':'not found'}), 404
    db.session.delete(i); db.session.commit()
    return jsonify({'ok': True})

# ── API: Export CSV ───────────────────────────────
@app.route('/api/export/<string:tipo>')
@login_required
def export_csv(tipo):
    from flask import Response
    import csv, io
    output = io.StringIO()
    if tipo == 'propiedades':
        w = csv.writer(output)
        w.writerow(['Dirección','Zona','Inquilino','DNI','Alquiler','Depósito','Inicio','Fin','Índice','Meses','Última Actualización'])
        for p in Propiedad.query.all():
            w.writerow([p.dir,p.zona,p.inquilino,p.dni,p.alquiler,p.deposito,p.inicio,p.fin,p.indice_actualizacion,p.meses_actualizacion,p.ultima_actualizacion])
    elif tipo == 'impuestos':
        w = csv.writer(output)
        w.writerow(['Propiedad','Tipo','Período','Monto','Vencimiento','Estado'])
        for i in Impuesto.query.all():
            w.writerow([i.prop_dir,i.tipo,i.periodo,i.monto,i.vto,i.estado])
    elif tipo == 'pagos':
        w = csv.writer(output)
        w.writerow(['Propiedad','Período','Monto Alquiler','Descuento','Neto Cobrado','Estado','Fecha Pago','Descripción','Nro Recibo'])
        for p in Pago.query.all():
            neto = p.monto - (p.descuento or 0)
            w.writerow([p.prop_dir,p.periodo,p.monto,p.descuento or 0,neto,p.estado,p.fecha_pago,p.descripcion or '',p.num_recibo])
    return Response('\ufeff'+output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={tipo}.csv'})

# ── Init & Run ────────────────────────────────────
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
