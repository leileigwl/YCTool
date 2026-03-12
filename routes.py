import os
from datetime import date, datetime
from flask import render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from database import db, allowed_file, create_app
from models import CompanyConfig, Customer, Product, Quotation, QuotationItem, Category
from sqlalchemy.orm import joinedload

def register_routes(app):

    # ===== 页面路由 =====
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/products')
    def products():
        return render_template('products.html')

    @app.route('/customers')
    def customers():
        return render_template('customers.html')

    @app.route('/categories')
    def categories():
        return render_template('categories.html')

    # ===== 公司配置 API =====
    @app.route('/api/company', methods=['GET'])
    def get_company():
        config = CompanyConfig.query.first()
        if config:
            return jsonify({
                'name_cn': config.name_cn,
                'name_en': config.name_en,
                'address_cn': config.address_cn,
                'address_en': config.address_en,
                'phone': config.phone,
                'email': config.email,
                'bank_name_cn': config.bank_name_cn,
                'bank_name_en': config.bank_name_en,
                'bank_account': config.bank_account,
                'bank_code': config.bank_code,
                'payment_note_cn': config.payment_note_cn,
                'payment_note_en': config.payment_note_en,
                'logo_path': config.logo_path
            })
        return jsonify({})

    @app.route('/api/company', methods=['PUT'])
    def update_company():
        config = CompanyConfig.query.first()
        if not config:
            config = CompanyConfig()
            db.session.add(config)

        data = request.json
        for field in ['name_cn', 'name_en', 'address_cn', 'address_en', 'phone', 'email',
                      'bank_name_cn', 'bank_name_en', 'bank_account', 'bank_code',
                      'payment_note_cn', 'payment_note_en']:
            if field in data:
                setattr(config, field, data[field])

        db.session.commit()
        return jsonify({'success': True})

    # ===== 客户 API =====
    @app.route('/api/customers', methods=['GET'])
    def get_customers():
        customers = Customer.query.order_by(Customer.created_at.desc()).all()
        return jsonify([{
            'id': c.id,
            'name_cn': c.name_cn,
            'name_en': c.name_en,
            'phone': c.phone,
            'address': c.address,
            'email': c.email
        } for c in customers])

    @app.route('/api/customers', methods=['POST'])
    def create_customer():
        data = request.json
        customer = Customer(
            name_cn=data.get('name_cn', ''),
            name_en=data.get('name_en', ''),
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            email=data.get('email', '')
        )
        db.session.add(customer)
        db.session.commit()
        return jsonify({'success': True, 'id': customer.id})

    @app.route('/api/customers/<int:id>', methods=['PUT'])
    def update_customer(id):
        customer = Customer.query.get_or_404(id)
        data = request.json
        for field in ['name_cn', 'name_en', 'phone', 'address', 'email']:
            if field in data:
                setattr(customer, field, data[field])
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/api/customers/<int:id>', methods=['DELETE'])
    def delete_customer(id):
        customer = Customer.query.get_or_404(id)
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'success': True})

    # ===== 分类 API =====
    @app.route('/api/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.sort_order).all()
        return jsonify([{
            'id': c.id,
            'name_cn': c.name_cn,
            'name_en': c.name_en,
            'sort_order': c.sort_order
        } for c in categories])

    @app.route('/api/categories', methods=['POST'])
    def create_category():
        data = request.json
        category = Category(
            name_cn=data.get('name_cn', ''),
            name_en=data.get('name_en', ''),
            sort_order=data.get('sort_order', 0)
        )
        db.session.add(category)
        db.session.commit()
        return jsonify({'success': True, 'id': category.id})

    @app.route('/api/categories/<int:id>', methods=['PUT'])
    def update_category(id):
        category = Category.query.get_or_404(id)
        data = request.json
        for field in ['name_cn', 'name_en', 'sort_order']:
            if field in data:
                setattr(category, field, data[field])
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/api/categories/<int:id>', methods=['DELETE'])
    def delete_category(id):
        category = Category.query.get_or_404(id)
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})

    # ===== 产品 API =====
    @app.route('/api/products', methods=['GET'])
    def get_products():
        products = Product.query.options(joinedload(Product.category)).order_by(Product.created_at.desc()).all()
        return jsonify([{
            'id': p.id,
            'name_cn': p.name_cn,
            'name_en': p.name_en,
            'image_path': p.image_path,
            'specification_cn': p.specification_cn,
            'specification_en': p.specification_en,
            'price': p.price,
            'currency': p.currency,
            'unit_cn': p.unit_cn,
            'unit_en': p.unit_en,
            'weight': p.weight,
            'volume': p.volume,
            'category_id': p.category_id,
            'category_name': p.category.name_cn if p.category else ''
        } for p in products])

    @app.route('/api/products', methods=['POST'])
    def create_product():
        data = request.json
        product = Product(
            name_cn=data.get('name_cn', ''),
            name_en=data.get('name_en', ''),
            specification_cn=data.get('specification_cn', ''),
            specification_en=data.get('specification_en', ''),
            price=float(data.get('price', 0)),
            currency=data.get('currency', 'CNY'),
            unit_cn=data.get('unit_cn', '件'),
            unit_en=data.get('unit_en', 'pcs'),
            weight=float(data.get('weight', 0)),
            volume=float(data.get('volume', 0)),
            category_id=data.get('category_id')
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True, 'id': product.id})

    @app.route('/api/products/<int:id>', methods=['PUT'])
    def update_product(id):
        product = Product.query.get_or_404(id)
        data = request.json
        for field in ['name_cn', 'name_en', 'specification_cn', 'specification_en',
                      'price', 'currency', 'unit_cn', 'unit_en', 'weight', 'volume', 'category_id']:
            if field in data:
                if field in ['price', 'weight', 'volume']:
                    setattr(product, field, float(data[field]))
                else:
                    setattr(product, field, data[field])
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/api/products/<int:id>', methods=['DELETE'])
    def delete_product(id):
        product = Product.query.get_or_404(id)
        if product.image_path:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/api/products/<int:id>/image', methods=['POST'])
    def upload_product_image(id):
        product = Product.query.get_or_404(id)

        if 'image' not in request.files:
            return jsonify({'error': 'No file'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            if product.image_path:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_path)
                if os.path.exists(old_path):
                    os.remove(old_path)

            filename = f'product_{id}_{secure_filename(file.filename)}'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            product.image_path = filename
            db.session.commit()

            return jsonify({'success': True, 'path': filename})

        return jsonify({'error': 'Invalid file type'}), 400

    # ===== 报价单 API =====
    @app.route('/api/quotation', methods=['POST'])
    def create_quotation():
        data = request.json

        today = date.today()
        prefix = f'QT-{today.strftime("%Y%m%d")}'
        count = Quotation.query.filter(
            Quotation.quotation_no.like(f'{prefix}%')
        ).count() + 1
        quotation_no = f'{prefix}-{count:03d}'

        quotation = Quotation(
            quotation_no=quotation_no,
            customer_id=data.get('customer_id'),
            date=datetime.strptime(data.get('date', today.isoformat()), '%Y-%m-%d').date(),
            valid_until=datetime.strptime(data.get('valid_until'), '%Y-%m-%d').date() if data.get('valid_until') else None,
            currency=data.get('currency', 'CNY'),
            remarks=data.get('remarks', '')
        )
        db.session.add(quotation)
        db.session.flush()

        items = data.get('items', [])
        total_price = 0
        total_weight = 0
        total_volume = 0

        for item in items:
            product = Product.query.get(item['product_id'])
            if product:
                qty = int(item.get('quantity', 1))
                price = float(item.get('price', product.price))

                quotation_item = QuotationItem(
                    quotation_id=quotation.id,
                    product_id=product.id,
                    quantity=qty,
                    price=price,
                    subtotal=price * qty,
                    weight=product.weight * qty,
                    volume=product.volume * qty
                )
                db.session.add(quotation_item)

                total_price += price * qty
                total_weight += product.weight * qty
                total_volume += product.volume * qty

        quotation.total_price = total_price
        quotation.total_weight = total_weight
        quotation.total_volume = total_volume

        db.session.commit()
        return jsonify({'success': True, 'id': quotation.id, 'quotation_no': quotation_no})

    @app.route('/api/quotations', methods=['GET'])
    def get_quotations():
        quotations = Quotation.query.options(joinedload(Quotation.customer)).order_by(Quotation.created_at.desc()).all()
        return jsonify([{
            'id': q.id,
            'quotation_no': q.quotation_no,
            'customer_name': q.customer.name_cn if q.customer else '',
            'date': q.date.isoformat(),
            'total_price': q.total_price,
            'currency': q.currency
        } for q in quotations])

    @app.route('/api/quotation/<int:id>', methods=['GET'])
    def get_quotation(id):
        quotation = Quotation.query.options(
            joinedload(Quotation.customer),
            joinedload(Quotation.items).joinedload(QuotationItem.product)
        ).get_or_404(id)
        return jsonify({
            'id': quotation.id,
            'quotation_no': quotation.quotation_no,
            'customer_id': quotation.customer_id,
            'customer': {
                'name_cn': quotation.customer.name_cn,
                'name_en': quotation.customer.name_en,
                'phone': quotation.customer.phone,
                'address': quotation.customer.address,
                'email': quotation.customer.email
            } if quotation.customer else None,
            'date': quotation.date.isoformat(),
            'valid_until': quotation.valid_until.isoformat() if quotation.valid_until else None,
            'currency': quotation.currency,
            'total_price': quotation.total_price,
            'total_weight': quotation.total_weight,
            'total_volume': quotation.total_volume,
            'remarks': quotation.remarks,
            'items': [{
                'product_id': item.product_id,
                'name_cn': item.product.name_cn,
                'name_en': item.product.name_en,
                'image_path': item.product.image_path,
                'specification_cn': item.product.specification_cn,
                'specification_en': item.product.specification_en,
                'quantity': item.quantity,
                'price': item.price,
                'subtotal': item.subtotal,
                'weight': item.weight,
                'volume': item.volume,
                'unit_cn': item.product.unit_cn,
                'unit_en': item.product.unit_en
            } for item in quotation.items]
        })

    @app.route('/api/quotation/<int:id>/pdf')
    def export_pdf(id):
        from utils.pdf_generator import generate_pdf
        return generate_pdf(id, request.args.get('lang', 'cn'))

    @app.route('/api/quotation/<int:id>/excel')
    def export_excel(id):
        from utils.excel_generator import generate_excel
        return generate_excel(id, request.args.get('lang', 'cn'))