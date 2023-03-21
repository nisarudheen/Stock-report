"""This module will help to create a daily report of stock
   (product name,product quantity) and email to inventory manager"""
from odoo import fields, models
import base64
import io
import xlsxwriter


class ProductInherit(models.Model):
    _name = 'stock.warning'
    _description = 'Stock Warning E-mail'
    today = fields.Date.today()

    def process_stock_warning(self):
        """we take details of product it is converted to
          Excel formate and attached to e-mail template sending
          to the mail administrator of inventory"""
        today = fields.Date.today()
        query = """select product_template.name->'en_US',stock_quant.quantity
         from product_template
         inner join product_product on product_product.product_tmpl_id=product_template.id
         inner join stock_quant on stock_quant.product_id = product_product.id"""
        self.env.cr.execute(query)
        table = self.env.cr.dictfetchall()
        manager = self.env['res.groups'].search(
            [('category_id', '=', 'Inventory')], limit=1)
        mail = manager.users.login
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_style = workbook.add_format({'align': 'center', 'bold': True})
        text_style = workbook.add_format({'align': 'center'})
        sheet = workbook.add_worksheet("Stock Report")
        sheet.set_column(1, 20, 25)
        sheet.merge_range('D1:G2', 'STOCK WARNING REPORT', header_style)
        sheet.merge_range('D4:D5', 'Report Date:', header_style)
        sheet.merge_range('E4:E5', str(today), header_style)
        sheet.merge_range('D8:E8', 'Product Name', header_style)
        sheet.merge_range('F8:G8', 'Quantity', header_style)
        row = 9
        for line in table:
            sheet.merge_range(f'D{row+1}:E{row+1}', line['?column?'], text_style)
            sheet.merge_range(f'F{row+1}:G{row+1}', line['quantity'], text_style)
            row += 1
        workbook.close()
        output.seek(0)
        excel = base64.b64encode(output.read())
        output.close()
        ir_values = {
            'name': 'Stock Report',
            'type': 'binary',
            'datas': excel,
            'store_fname': excel,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'stock.warning',
        }
        attachment = self.env['ir.attachment'].sudo().create(ir_values)
        email_template = self.env.ref(
            'stock_warning.stock_warning_email_template')
        email_values = {
            'email_to': mail,
            'email_from': self.env.user.email
        }
        email_template.attachment_ids = [(4, attachment.id)]
        email_template.send_mail(self.id, email_values=email_values,
                                 force_send=True)
        email_template.attachment_ids = [(5, 0, 0)]



