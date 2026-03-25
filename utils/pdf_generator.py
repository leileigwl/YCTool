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
    # 获取项目根目录下的字体路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_paths = [
        # 项目内置字体（优先）
        os.path.join(project_root, 'static', 'fonts', 'SourceHanSansCN-Regular.otf'),
        # macOS 系统字体
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
        # Linux 常见字体路径
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('Chinese', path))
                return 'Chinese'
            except Exception as e:
                print(f"Failed to load font {path}: {e}")
                continue
    print("WARNING: No Chinese font found, using Helvetica (Chinese characters will not display)")
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
    """生成PDF - 使用多个表格避免SPAN和INNERGRID冲突"""
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
            'bill_to': 'Bill To', 'contact': 'Contact', 'no': 'No.', 'image': 'Image',
            'description': 'Description', 'specification': 'Specification',
            'unit_price': 'Unit Price', 'quantity': 'Qty', 'unit': 'Unit',
            'amount': 'Amount', 'weight': 'Weight(kg)', 'volume': 'Volume(m³)',
            'total': 'TOTAL', 'remarks': 'Remarks', 'bank_info': 'Bank Information',
            'thank_you': 'Thank you for your business!'
        }
    else:
        texts = {
            'quotation': '报价单', 'date': '日期', 'valid_until': '有效期至',
            'bill_to': '买方信息', 'contact': '联系人', 'no': '序号', 'image': '图片',
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
    info_value_style = ParagraphStyle('InfoValue', fontName=CHINESE_FONT, fontSize=9,
                                       textColor=HEADER_BG, alignment=1, leading=12)
    header_style = ParagraphStyle('Header', fontName=CHINESE_FONT, fontSize=8,
                                   textColor=HEADER_TEXT, alignment=1, leading=10, wordWrap='CJK')
    cell_style = ParagraphStyle('Cell', fontName=CHINESE_FONT, fontSize=7, alignment=1, leading=9)
    cell_left_style = ParagraphStyle('CellLeft', fontName=CHINESE_FONT, fontSize=7, alignment=0, leading=9)
    total_label_style = ParagraphStyle('TotalLabel', fontName=CHINESE_FONT, fontSize=9,
                                        textColor=colors.black, alignment=1, leading=12)
    total_value_style = ParagraphStyle('TotalValue', fontName=CHINESE_FONT, fontSize=9,
                                        textColor=HEADER_BG, alignment=1, leading=12)
    footer_style = ParagraphStyle('Footer', fontName=CHINESE_FONT, fontSize=8, alignment=0, leading=10)

    company_name_cn = company.name_cn or ''
    company_name_en = company.name_en or ''
    customer = quotation.customer

    # ===== 列宽定义 =====
    col_widths = [1.4*cm, 2.5*cm, 2.4*cm, 3.8*cm, 1.8*cm, 1.5*cm, 1.3*cm, 1.8*cm, 1.6*cm, 1.6*cm]
    total_width = sum(col_widths)

    # ===== 表格1: 公司名称行 =====
    # 中文版：只显示中文名
    # 英文版：只显示英文名
    if lang == 'en':
        company_full_name = company_name_en or company_name_cn
    else:
        company_full_name = company_name_cn

    company_name = company_name_en if lang == 'en' and company_name_en else company_name_cn

    company_data = [[Paragraph(f'<b>{company_full_name}</b>', company_style)]]
    company_table = Table(company_data, colWidths=[total_width])
    company_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), COMPANY_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(company_table)

    # ===== 表格2: 报价单号行 =====
    quotation_data = [[Paragraph(f'<b>{texts["quotation"]}</b>: {quotation.quotation_no}', info_value_style)]]
    quotation_table = Table(quotation_data, colWidths=[total_width])
    quotation_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(quotation_table)

    # ===== 表格3: 买方信息行 =====
    if customer:
        name = get_localized(customer, 'name', lang)
        bill_data = [[Paragraph(f'<b>{texts["bill_to"]}</b>: {name}', info_value_style)]]
        bill_table = Table(bill_data, colWidths=[total_width])
        bill_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(bill_table)

        # 联系人行
        contacts = []
        if customer.phone:
            contacts.append(customer.phone)
        if customer.email:
            contacts.append(customer.email)
        contact_str = ' / '.join(contacts) if contacts else '-'
        contact_data = [[Paragraph(f'<b>{texts["contact"]}</b>: {contact_str}', info_value_style)]]
        contact_table = Table(contact_data, colWidths=[total_width])
        contact_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(contact_table)

    # ===== 表格4: 日期行 =====
    date_text = f'<b>{texts["date"]}</b>: {quotation.date}'
    if quotation.valid_until:
        date_text += f'  |  <b>{texts["valid_until"]}</b>: {quotation.valid_until}'
    date_data = [[Paragraph(date_text, info_value_style)]]
    date_table = Table(date_data, colWidths=[total_width])
    date_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(date_table)

    # ===== 表格5: 产品表（表头+数据+合计）- 这个表格需要竖线 =====
    product_data = []

    # 表头行
    product_data.append([
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
    for idx, item in enumerate(quotation.items, 1):
        name = get_localized(item.product, 'name', lang)
        spec = get_localized(item.product, 'specification', lang)
        unit = get_localized(item.product, 'unit', lang)

        # 图片
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

        product_data.append([
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

    # 合计行 - 合并前6列
    total_row_data = ['', '', '', '', '', '']
    total_row_data.append(Paragraph(f'<b>{texts["total"]}</b>', total_label_style))
    total_row_data.append(Paragraph(f'<b>{currency_symbol}{quotation.total_price:.2f}</b>', total_value_style))
    total_row_data.append(Paragraph(f'<b>{quotation.total_weight:.2f}</b>', total_value_style))
    total_row_data.append(Paragraph(f'<b>{quotation.total_volume:.3f}</b>', total_value_style))
    product_data.append(total_row_data)

    # 创建产品表格
    product_table = Table(product_data, colWidths=col_widths)

    # 产品表格样式 - 使用GRID显示网格线
    product_style = [
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # 使用黑色网格线，宽度1
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),

        # 表头行样式
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HEADER_TEXT),

        # 合计行样式
        ('BACKGROUND', (0, -1), (-1, -1), LIGHT_BLUE),
    ]

    # 数据行交替颜色
    for i in range(1, len(product_data) - 1):
        if i % 2 == 0:
            product_style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_GRAY))

    product_table.setStyle(TableStyle(product_style))
    elements.append(product_table)

    # ===== 表格6: 备注行 =====
    if quotation.remarks:
        remarks_data = [[Paragraph(f'<b>{texts["remarks"]}</b>: {quotation.remarks}', footer_style)]]
        remarks_table = Table(remarks_data, colWidths=[total_width])
        remarks_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(remarks_table)

    # ===== 表格7: 银行信息行 =====
    bank_name = get_localized(company, 'bank_name', lang)
    bank_text = f"<b>{texts['bank_info']}</b>: {bank_name or ''}"
    if company.bank_account:
        bank_text += f"  |  账号: {company.bank_account}"
    if company.bank_code:
        bank_text += f"  |  SWIFT: {company.bank_code}"
    bank_data = [[Paragraph(bank_text, footer_style)]]
    bank_table = Table(bank_data, colWidths=[total_width])
    bank_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(bank_table)

    # 页脚
    elements.append(Spacer(1, 0.3*cm))
    footer_text_style = ParagraphStyle('FooterText', fontName=CHINESE_FONT, fontSize=9, alignment=1)
    elements.append(Paragraph(f'<b>{company_name}</b>', footer_text_style))
    thank_you_style = ParagraphStyle('ThankYou', fontName=CHINESE_FONT, fontSize=8, alignment=1, textColor=colors.grey)
    elements.append(Paragraph(f'<i>{texts["thank_you"]}</i>', thank_you_style))

    doc.build(elements)
    return send_file(pdf_path, as_attachment=True, download_name=f'{quotation.quotation_no}.pdf')