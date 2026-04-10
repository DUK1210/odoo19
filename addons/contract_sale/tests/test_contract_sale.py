from odoo.tests.common import TransactionCase, Form
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import datetime, timedelta


class TestContractSale(TransactionCase):

    def setUp(self):
        super(TestContractSale, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })
        self.product1 = self.env['product.product'].create({
            'name': 'Test Product 1',
            'type': 'product',
            'lst_price': 100.0,
        })
        self.product2 = self.env['product.product'].create({
            'name': 'Test Product 2',
            'type': 'product',
            'lst_price': 200.0,
        })
        self.uom_unit = self.env.ref('uom.product_uom_unit')

    def test_create_contract(self):
        """Test creating a contract"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        self.assertEqual(contract.state, 'draft')
        self.assertEqual(contract.qty_contract, 100)

    def test_contract_confirm(self):
        """Test confirming a contract"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()
        self.assertEqual(contract.state, 'active')

    def test_contract_confirm_without_lines(self):
        """Test that contract cannot be confirmed without lines"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
        })
        with self.assertRaises(UserError):
            contract.action_confirm()

    def test_contract_confirm_expired(self):
        """Test that expired contract cannot be confirmed"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today() - timedelta(days=60),
            'date_end': datetime.today() - timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        with self.assertRaises(UserError):
            contract.action_confirm()

    def test_sale_order_exceed_contract_qty(self):
        """Test that SO cannot exceed contract quantity"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()

        # Try to create SO with quantity > contract
        with self.assertRaises(UserError):
            so = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'contract_id': contract.id,
                'order_line': [(0, 0, {
                    'product_id': self.product1.id,
                    'product_uom_qty': 150,  # Exceeds contract
                    'price_unit': 100.0,
                })],
            })
            so.action_confirm()

    def test_sale_order_valid_qty(self):
        """Test valid SO within contract limits"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()

        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'contract_id': contract.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 50,
                'price_unit': 100.0,
            })],
        })
        so.action_confirm()
        self.assertEqual(so.state, 'sale')
        
        # Check contract qty_sold updated
        contract_line = contract.line_ids[0]
        self.assertEqual(contract_line.qty_sold, 50)
        self.assertEqual(contract_line.qty_remaining, 50)

    def test_sale_order_cancel_rollback(self):
        """Test that cancelling SO rolls back contract quantities"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()

        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'contract_id': contract.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 50,
                'price_unit': 100.0,
            })],
        })
        so.action_confirm()
        
        # Cancel SO
        so._action_cancel()
        
        # Check contract rolled back
        contract_line = contract.line_ids[0]
        self.assertEqual(contract_line.qty_sold, 0)
        self.assertEqual(contract_line.qty_remaining, 100)

    def test_purchase_order_exceed_so_qty(self):
        """Test that PO cannot exceed SO quantity"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()

        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'contract_id': contract.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 50,
                'price_unit': 100.0,
            })],
        })
        so.action_confirm()

        # Try to create PO with quantity > SO
        vendor = self.env['res.partner'].create({'name': 'Test Vendor', 'supplier_rank': 1})
        with self.assertRaises(UserError):
            po = self.env['purchase.order'].create({
                'partner_id': vendor.id,
                'sale_order_id': so.id,
                'order_line': [(0, 0, {
                    'product_id': self.product1.id,
                    'product_qty': 60,  # Exceeds SO
                    'price_unit': 50.0,
                })],
            })
            po.button_confirm()

    def test_contract_remaining_calculation(self):
        """Test contract remaining quantity calculation"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()

        # Create first SO
        so1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'contract_id': contract.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 30,
                'price_unit': 100.0,
            })],
        })
        so1.action_confirm()

        # Check remaining
        contract_line = contract.line_ids[0]
        self.assertEqual(contract_line.qty_remaining, 70)

        # Create second SO
        so2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'contract_id': contract.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 40,
                'price_unit': 100.0,
            })],
        })
        so2.action_confirm()

        # Check remaining
        self.assertEqual(contract_line.qty_remaining, 30)

    def test_contract_product_not_in_contract(self):
        """Test that SO cannot include products not in contract"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()

        with self.assertRaises(UserError):
            so = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'contract_id': contract.id,
                'order_line': [(0, 0, {
                    'product_id': self.product2.id,  # Not in contract
                    'product_uom_qty': 10,
                    'price_unit': 200.0,
                })],
            })
            so.action_confirm()

    def test_contract_partner_mismatch(self):
        """Test that SO customer must match contract customer"""
        other_partner = self.env['res.partner'].create({'name': 'Other Customer'})
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()

        with self.assertRaises(ValidationError):
            self.env['sale.order'].create({
                'partner_id': other_partner.id,  # Different from contract
                'contract_id': contract.id,
                'order_line': [(0, 0, {
                    'product_id': self.product1.id,
                    'product_uom_qty': 10,
                    'price_unit': 100.0,
                })],
            })

    def test_contract_progress_bar(self):
        """Test contract progress bar colors"""
        contract = self.env['contract.sale'].create({
            'partner_id': self.partner.id,
            'date_start': datetime.today(),
            'date_end': datetime.today() + timedelta(days=30),
            'line_ids': [(0, 0, {
                'product_id': self.product1.id,
                'qty_contract': 100,
                'price_unit': 100.0,
                'uom_id': self.uom_unit.id,
            })],
        })
        contract.action_confirm()

        # Progress < 80% should be success
        self.assertEqual(contract.line_ids[0].get_progress_color(), 'success')

        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'contract_id': contract.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 85,
                'price_unit': 100.0,
            })],
        })
        so.action_confirm()

        # Progress 80-99% should be warning
        self.assertEqual(contract.line_ids[0].get_progress_color(), 'warning')

        # Create another SO to exceed 100%
        so2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'contract_id': contract.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 15,
                'price_unit': 100.0,
            })],
        })
        so2.action_confirm()

        # Progress >= 100% should be danger
        self.assertEqual(contract.line_ids[0].get_progress_color(), 'danger')
