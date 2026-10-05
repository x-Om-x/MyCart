import io
import json
import re
from html import escape

from django.core import signing
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Order, Product, Contact, OrderUpdate
from math import ceil

def index(request):

    
    #params = {'no_of_slide':n_slides , 'range': range(1, n_slides),'product':products}
    #all_prods = [[products, range(1,len(products)), n_slides],[products, range(1,len(products)), n_slides]]
    all_prods = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category = cat)
        n = len(prod)
        n_slides = n//4 + ceil((n/4) - n//4)
        all_prods.append([prod, range(1, n_slides), n_slides])

    params = {'all_prods':all_prods}
    return render(request, 'shop/index.html', params)
def search_products(query):
    products_by_category = {}
    matching_products = Product.objects.filter(
        Q(product_name__icontains=query)
        | Q(desc__icontains=query)
        | Q(category__icontains=query)
    ).order_by('category')

    for product in matching_products:
        products_by_category.setdefault(product.category, []).append(product)

    grouped_products = []
    for products in products_by_category.values():
        n_slides = ceil(len(products) / 4)
        grouped_products.append([products, range(1, n_slides), n_slides])
    return grouped_products


def search(request):
    query = request.GET.get('search', '').strip()
    all_prods = search_products(query) if query else []
    return render(request, 'shop/index.html', {
        'all_prods': all_prods,
        'query': query,
    })

def about(request):
    return render(request, 'shop/about.html')

def contact(request):
    if request.method == "POST":
        name = (request.POST.get('name', '') or '').strip()
        email = (request.POST.get('email', '') or '').strip()
        phone = (request.POST.get('phone', '') or '').strip()
        desc = (request.POST.get('message', '') or '').strip()

        if not all([name, email, desc]):
            return HttpResponseBadRequest('Please complete the required contact fields.')

        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
    return render(request, 'shop/contact.html')

def tracker(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id', '')
        email = request.POST.get('email', '')
        try:
            order_id = int(order_id)
            order = Order.objects.get(order_id=order_id, email=email)
        except (ValueError, TypeError, Order.DoesNotExist):
            return JsonResponse(
                {'error': 'No order was found with that Order ID and email.'},
                status=404,
            )

        try:
            updates = [
                {'text': item.update_desc, 'time': item.timestamp}
                for item in OrderUpdate.objects.filter(order_id=order_id)
            ]
            return JsonResponse([updates, order.items_json], safe=False)
        except Exception:
            return JsonResponse(
                {'error': 'Unable to track this order right now.'},
                status=500,
            )

    return render(request, 'shop/tracker.html')

       




def prod_view(request, myid):
    product = get_object_or_404(Product, id=myid)
    return render(request, 'shop/prod_view.html', {'product': product})

def checkout(request):
    if request.method == "POST":
        try:
            submitted_items = json.loads(request.POST.get('itemsJson', ''))
            if not isinstance(submitted_items, dict) or not submitted_items:
                raise ValueError

            product_quantities = {}
            for cart_key, cart_item in submitted_items.items():
                match = re.fullmatch(r'pr(\d+)', cart_key)
                if not match or not isinstance(cart_item, list) or not cart_item:
                    raise ValueError
                quantity = int(cart_item[0])
                if quantity < 1:
                    raise ValueError
                product_quantities[int(match.group(1))] = quantity

            products = Product.objects.in_bulk(product_quantities)
            if len(products) != len(product_quantities):
                raise ValueError

            name = (request.POST.get('name', '') or '').strip()
            email = (request.POST.get('email', '') or '').strip()
            address1 = (request.POST.get('address1', '') or '').strip()
            address2 = (request.POST.get('address2', '') or '').strip()
            city = (request.POST.get('city', '') or '').strip()
            state = (request.POST.get('state', '') or '').strip()
            zip_code = (request.POST.get('zip_code', '') or '').strip()
            phone = (request.POST.get('phone', '') or '').strip()

            if not all([name, email, address1, city, state, zip_code, phone]):
                raise ValueError

        except (ValueError, TypeError, json.JSONDecodeError):
            return HttpResponseBadRequest('Your cart is invalid. Please review it and try again.')

        items = {}
        amount = 0
        for product_id, quantity in product_quantities.items():
            product = products[product_id]
            items[f'pr{product_id}'] = [quantity, product.product_name, product.price]
            amount += quantity * product.price

        order = Order.objects.create(
            items_json=json.dumps(items),
            name=name,
            amount=amount,
            email=email,
            address=' '.join(filter(None, [address1, address2])),
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
        )
        OrderUpdate.objects.create(
            order_id=order.order_id,
            update_desc='The order has been placed',
        )
        pdf_token = signing.TimestampSigner().sign(str(order.order_id))
        return render(request, 'shop/order_confirmation.html', {
            'order': order,
            'pdf_token': pdf_token,
        })
    return render(request, 'shop/checkout.html')


def order_invoice(request, token):
    try:
        order_id = signing.TimestampSigner().unsign(token, max_age=60 * 60 * 24)
        order = get_object_or_404(Order, order_id=int(order_id))
    except (signing.BadSignature, ValueError):
        raise Http404('Invoice not found')

    items = json.loads(order.items_json)
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.7 * inch,
        title=f'MyCart Order Invoice {order.order_id}',
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='InvoiceRight', parent=styles['Normal'], alignment=TA_RIGHT))
    elements = [
        Paragraph('MyCart', styles['Title']),
        Paragraph('ORDER INVOICE', styles['Heading2']),
        Spacer(1, 10),
    ]

    invoice_details = [
        [Paragraph(f'<b>Order ID:</b> {order.order_id}', styles['Normal']),
         Paragraph(f'<b>Issued:</b> {timezone.localtime().strftime("%d %b %Y, %H:%M %Z")}', styles['InvoiceRight'])],
        [Paragraph(f'<b>Customer:</b> {escape(order.name)}', styles['Normal']),
         Paragraph(f'<b>Email:</b> {escape(order.email)}', styles['InvoiceRight'])],
        [Paragraph(f'<b>Phone:</b> {escape(order.phone)}', styles['Normal']),
         Paragraph(f'<b>Shipping address:</b> {escape(", ".join(filter(None, [order.address, order.city, order.state, order.zip_code])))}', styles['InvoiceRight'])],
    ]
    details_table = Table(invoice_details, colWidths=[3.55 * inch, 3.05 * inch])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    elements.extend([details_table, Spacer(1, 14)])

    item_rows = [[
        Paragraph('<b>Product</b>', styles['Normal']),
        Paragraph('<b>Qty</b>', styles['Normal']),
        Paragraph('<b>Unit price</b>', styles['Normal']),
        Paragraph('<b>Line total</b>', styles['Normal']),
    ]]
    for item in items.values():
        quantity, name, unit_price = item
        item_rows.append([
            Paragraph(escape(str(name)), styles['Normal']),
            str(quantity),
            f'INR {unit_price}',
            f'INR {quantity * unit_price}',
        ])

    item_table = Table(item_rows, colWidths=[3.2 * inch, 0.55 * inch, 1.35 * inch, 1.5 * inch], repeatRows=1)
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef2')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c8d0d6')),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    elements.extend([item_table, Spacer(1, 16)])

    totals = Table([
        ['Subtotal', f'INR {order.amount}'],
        ['Delivery', 'INR 0'],
        [Paragraph('<b>Total amount due</b>', styles['Normal']),
         Paragraph(f'<b>INR {order.amount}</b>', styles['InvoiceRight'])],
    ], colWidths=[5.1 * inch, 1.5 * inch], hAlign='RIGHT')
    totals.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.HexColor('#263746')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.extend([
        totals,
        Spacer(1, 20),
        Paragraph('<b>Payment method:</b> Manual/offline payment', styles['Normal']),
        Paragraph('<b>Payment status:</b> Pending', styles['Normal']),
    ])

    document.build(elements)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="mycart-invoice-{order.order_id}.pdf"'
    return response
    
