import os
from flask import send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from models import Quotation, CompanyConfig

# 注册中文字体
def register_chinese_font():
    font_paths = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('Chinese', path))
                return 'Chinese'
            except:
                continue
    return 'Helvetica'

CHINESE_FONT = register_chinese_font()

# 配色 - 参考图片的蓝色
HEADER_BG = colors.HexColor('#1F4E79')  # 深蓝色表头
HEADER_TEXT = colors.white
LIGHT_BLUE = colors.HexColor('#BDD7EE')  # 浅蓝色背景
LIGHT_GRAY = colors.HexColor('#F2F2F2')  # 浅灰色
COMPANY_BG = colors.HexColor('#2E75B6')  # 公司名称背景色
BORDER_COLOR = colors.HexColor('#1F4E79')

def get_localized(obj, field_base, lang):
    en_val = getattr(obj, f'{field_base}_en', None)
    return en_val if lang == 'en' and en_val else getattr(obj, f'{field_base}_cn', '')

def generate_pdf(quotation_id, lang='cn'):
    """生成PDF - 参考图片格式"""
    quotation = Quotation.query.get_or_404(quotation_id)
    company = CompanyConfig.query.first()

    pdf_path = os.path.join(os.getcwd(), 'static', 'uploads', f'quotation_{quotation_id}.pdf')

    # A4窄边距
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        topMargin=0.5*cm,
        bottomMargin=0.5*cm,
        leftMargin=0.8*cm,
        rightMargin=0.8*cm
    )

    elements = []

    # 语言文本
    if lang == 'en':
        texts = {
            'quotation': 'QUOTATION', 'date': 'Date', 'valid_until': 'Valid Until',
            'bill_to': 'Bill To', 'no': 'No.', 'image': 'Image',
            'description': 'Description', 'specification': 'Specification',
            'unit_price': 'Unit Price', 'quantity': 'Qty', 'unit': 'Unit',
            'amount': 'Amount', 'weight': 'Weight(kg)', 'volume': 'Volume(m³)',
            'total': 'TOTAL', 'remarks': 'Remarks', 'bank_info': 'Bank Information',
            'thank_you': 'Thank you for your business!'
        }
    else:
        texts = {
            'quotation': '报价单', 'date': '日期', 'valid_until': '有效期至',
            'bill_to': '买方信息', 'no': '序号', 'image': '图片',
            'description': '商品名称', 'specification': '规格',
            'unit_price': '单价', 'quantity': '数量', 'unit': '单位',
            'amount': '金额', 'weight': '重量(kg)', 'volume': '体积(m³)',
            'total': '合计', 'remarks': '备注', 'bank_info': '银行信息',
            'thank_you': '感谢您的惠顾！'
        }

    currency_symbol = '$' if quotation.currency == 'USD' else '¥'

    # 样式定义
    company_style = ParagraphStyle('Company', fontName=CHINESE_FONT, fontSize=14,
                                    textColor=colors.white, alignment=1, leading=18)
    contact_style = ParagraphStyle('Contact', fontName=CHINESE_FONT, fontSize=8,
                                    textColor=colors.black, alignment=1, leading=10)
    info_label_style = ParagraphStyle('InfoLabel', fontName=CHINESE_FONT, fontSize=9,
                                       textColor=colors.black, alignment=1, leading=12)
    info_value_style = ParagraphStyle('InfoValue', fontName=CHINESE_FONT, fontSize=9,
                                       textColor=HEADER_BG, alignment=1, leading=12)
    bill_label_style = ParagraphStyle('BillLabel', fontName=CHINESE_FONT, fontSize=9,
                                        textColor=colors.black, alignment=0, leading=12)
    bill_value_style = ParagraphStyle('BillValue', fontName=CHINESE_FONT, fontSize=9,
                                        textColor=HEADER_BG, alignment=0, leading=12)
    header_style = ParagraphStyle('Header', fontName=CHINESE_FONT, fontSize=8,
                                   textColor=HEADER_TEXT, alignment=1, leading=10, wordWrap='CJK')
    cell_style = ParagraphStyle('Cell', fontName=CHINESE_FONT, fontSize=7, alignment=1, leading=9)
    cell_left_style = ParagraphStyle('CellLeft', fontName=CHINESE_FONT, fontSize=7, alignment=0, leading=9)
    total_label_style = ParagraphStyle('TotalLabel', fontName=CHINESE_FONT, fontSize=9,
                                        textColor=colors.black, alignment=1, leading=12)
    total_value_style = ParagraphStyle('TotalValue', fontName=CHINESE_FONT, fontSize=9,
                                        textColor=HEADER_BG, alignment=1, leading=12)
    footer_style = ParagraphStyle('Footer', fontName=CHINESE_FONT, fontSize=8, alignment=0, leading=10)

    company_name = get_localized(company, 'name', lang)
    company_name_en = company.name_en if company.name_en else ''
    company_address = get_localized(company, 'address', lang)
    customer = quotation.customer

    # ===== 列宽定义 - 确保表头文字横向显示在一行 =====
    # 序号:图片:名称:规格:单价:数量:单位:金额:重量:体积
    # 每列都要足够宽让文字横向显示
    col_widths = [1.2*cm, 2.5*cm, 2.2*cm, 4.0*cm, 1.8*cm, 1.4*cm, 1.2*cm, 1.8*cm, 1.6*cm, 1.6*cm]
    # 总和约19.3cm

    # ===== 构建表格数据 =====
    table_data = []

    # 第1行：公司名称（蓝色背景）
    company_full_name = f"{company_name}"
    if company_name_en:
        company_full_name = f"{company_name}<br/>{company_name_en}"
    table_data.append([Paragraph(f'<b>{company_full_name}</b>', company_style)] + [''] * 9)

    # 第2行：报价单号
    table_data.append([
        Paragraph(f'<b>{texts["quotation"]}</b>: {quotation.quotation_no}', info_value_style),
        '', '', '', '', '', '', '', '', ''
    ])

    # 第3行：买方（单独一行）
    if customer:
        name = get_localized(customer, 'name', lang)
        table_data.append([
            Paragraph(f'<b>{texts["bill_to"]}</b>: {name}', info_value_style),
            '', '', '', '', '', '', '', '', ''
        ])

    # 第4行：联系人（单独一行）
    if customer:
        contacts = []
        if customer.phone:
            contacts.append(customer.phone)
        if customer.email:
            contacts.append(customer.email)
        contact_str = ' / '.join(contacts) if contacts else '-'
        table_data.append([
            Paragraph(f'<b>联系人</b>: {contact_str}', info_value_style),
            '', '', '', '', '', '', '', '', ''
        ])

    # 第5行：交易日期（如有有效期则用竖线分隔）
    date_text = f'<b>{texts["date"]}</b>: {quotation.date}'
    if quotation.valid_until:
        date_text += f'  |  <b>{texts["valid_until"]}</b>: {quotation.valid_until}'
    table_data.append([
        Paragraph(date_text, info_value_style),
        '', '', '', '', '', '', '', '', ''
    ])

    # 产品表头
    table_data.append([
        Paragraph(texts['no'], header_style),
        Paragraph(texts['image'], header_style),
        Paragraph(texts['description'], header_style),
        Paragraph(texts['specification'], header_style),
        Paragraph(texts['unit_price'], header_style),
        Paragraph(texts['quantity'], header_style),
        Paragraph(texts['unit'], header_style),
        Paragraph(texts['amount'], header_style),
        Paragraph(texts['weight'], header_style),
        Paragraph(texts['volume'], header_style)
    ])

    # 产品数据行
    row_idx = 0
    for idx, item in enumerate(quotation.items, 1):
        name = get_localized(item.product, 'name', lang)
        spec = get_localized(item.product, 'specification', lang)
        unit = get_localized(item.product, 'unit', lang)

        # 图片 - 放大到2.5cm让客户看清
        img_cell = '-'
        if item.product.image_path:
            img_path = os.path.join(os.getcwd(), 'static', 'uploads', item.product.image_path)
            if os.path.exists(img_path):
                try:
                    img = Image(img_path, width=2.5*cm, height=2.5*cm)
                    img_cell = img
                except:
                    img_cell = '-'

        spec_text = (spec or '-').replace('\n', '<br/>')

        # 每行的重量和体积
        row_weight = item.weight if item.weight else (item.product.weight or 0) * item.quantity
        row_volume = item.volume if item.volume else (item.product.volume or 0) * item.quantity

        table_data.append([
            Paragraph(str(idx), cell_style),
            img_cell,
            Paragraph(name, cell_style),
            Paragraph(spec_text, cell_left_style),
            Paragraph(f"{currency_symbol}{item.price:.2f}", cell_style),
            Paragraph(str(item.quantity), cell_style),
            Paragraph(unit, cell_style),
            Paragraph(f"{currency_symbol}{item.subtotal:.2f}", cell_style),
            Paragraph(f"{row_weight:.2f}", cell_style),
            Paragraph(f"{row_volume:.3f}", cell_style)
        ])
        row_idx += 1

    # 合计行 - 不合并，每列单独显示
    table_data.append([
        '', '', '', '', '', '',
        Paragraph(f'<b>{texts["total"]}</b>', total_label_style),
        Paragraph(f'<b>{currency_symbol}{quotation.total_price:.2f}</b>', total_value_style),
        Paragraph(f'<b>{quotation.total_weight:.2f}</b>', total_value_style),
        Paragraph(f'<b>{quotation.total_volume:.3f}</b>', total_value_style)
    ])

    # 备注行
    if quotation.remarks:
        table_data.append([Paragraph(f'<b>{texts["remarks"]}</b>: {quotation.remarks}', footer_style)] + [''] * 9)

    # 银行信息行
    bank_name = get_localized(company, 'bank_name', lang)
    bank_text = f"<b>{texts['bank_info']}</b>: {bank_name or ''}"
    if company.bank_account:
        bank_text += f"  |  账号: {company.bank_account}"
    if company.bank_code:
        bank_text += f"  |  SWIFT: {company.bank_code}"
    table_data.append([Paragraph(bank_text, footer_style)] + [''] * 9)

    # 创建表格
    main_table = Table(table_data, colWidths=col_widths)

    # 行索引计算
    company_row = 0
    quotation_row = 1
    bill_row = 2 if customer else None
    contact_person_row = 3 if customer else None
    date_row = 4 if customer else 1
    header_row = 5 if customer else 2
    data_start_row = header_row + 1
    data_end_row = header_row + len(quotation.items)
    total_row = data_end_row + 1
    remarks_row = total_row + 1 if quotation.remarks else None
    bank_row = remarks_row + 1 if quotation.remarks else total_row + 1

    # 样式命令
    style_commands = [
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.8, BORDER_COLOR),  # 内部网格线（竖线和横线）
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),

        # 公司名称行 - 蓝色背景
        ('BACKGROUND', (0, company_row), (-1, company_row), COMPANY_BG),
        ('TEXTCOLOR', (0, company_row), (-1, company_row), colors.white),
        ('SPAN', (0, company_row), (9, company_row)),

        # 报价单号行
        ('SPAN', (0, quotation_row), (9, quotation_row)),
        ('BACKGROUND', (0, quotation_row), (-1, quotation_row), LIGHT_BLUE),

        # 表头行 - 深蓝色背景
        ('BACKGROUND', (0, header_row), (-1, header_row), HEADER_BG),
        ('TEXTCOLOR', (0, header_row), (-1, header_row), HEADER_TEXT),

        # 合计行 - 浅蓝色背景（合并前6列）
        ('BACKGROUND', (0, total_row), (-1, total_row), LIGHT_BLUE),
        ('SPAN', (0, total_row), (5, total_row)),
    ]

    # 买方行样式
    if bill_row is not None:
        style_commands.append(('SPAN', (0, bill_row), (9, bill_row)))
        style_commands.append(('BACKGROUND', (0, bill_row), (-1, bill_row), LIGHT_GRAY))

    # 联系人行样式
    if contact_person_row is not None:
        style_commands.append(('SPAN', (0, contact_person_row), (9, contact_person_row)))
        style_commands.append(('BACKGROUND', (0, contact_person_row), (-1, contact_person_row), LIGHT_GRAY))

    # 交易日期行样式
    style_commands.append(('SPAN', (0, date_row), (9, date_row)))
    style_commands.append(('BACKGROUND', (0, date_row), (-1, date_row), LIGHT_BLUE))

    if remarks_row is not None:
        style_commands.append(('SPAN', (0, remarks_row), (9, remarks_row)))
        style_commands.append(('BACKGROUND', (0, remarks_row), (-1, remarks_row), LIGHT_GRAY))

    style_commands.append(('SPAN', (0, bank_row), (9, bank_row)))
    style_commands.append(('BACKGROUND', (0, bank_row), (-1, bank_row), LIGHT_GRAY))

    # 数据行交替颜色
    for i, row_num in enumerate(range(data_start_row, data_end_row + 1)):
        if i % 2 == 1:
            style_commands.append(('BACKGROUND', (0, row_num), (-1, row_num), LIGHT_GRAY))

    main_table.setStyle(TableStyle(style_commands))
    elements.append(main_table)

    # 页脚
    elements.append(Spacer(1, 0.3*cm))
    footer_text_style = ParagraphStyle('FooterText', fontName=CHINESE_FONT, fontSize=9, alignment=1)
    elements.append(Paragraph(f'<b>{company_name}</b>', footer_text_style))
    thank_you_style = ParagraphStyle('ThankYou', fontName=CHINESE_FONT, fontSize=8, alignment=1, textColor=colors.grey)
    elements.append(Paragraph(f'<i>{texts["thank_you"]}</i>', thank_you_style))

    doc.build(elements)
    return send_file(pdf_path, as_attachment=True, download_name=f'{quotation.quotation_no}.pdf')