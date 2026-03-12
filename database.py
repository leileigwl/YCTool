import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

db = SQLAlchemy()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'quotation.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size

    # 确保上传目录存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        # 导入模型以确保表被创建
        from models import CompanyConfig, Customer, Product, Quotation, QuotationItem, Category
        db.create_all()
        # 初始化公司配置
        if not CompanyConfig.query.first():
            default_config = CompanyConfig(
                name_cn='远成国际进出口贸易有限公司',
                name_en='Yuan Cheng International Import & Export Co., Ltd',
                address_cn='',
                address_en='',
                phone='',
                email='',
                bank_name_cn='',
                bank_name_en='',
                bank_account='',
                bank_code='',
                payment_note_cn='',
                payment_note_en='',
                logo_path=''
            )
            db.session.add(default_config)
            db.session.commit()

    from routes import register_routes
    register_routes(app)

    return app