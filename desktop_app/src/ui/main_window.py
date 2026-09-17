import sys
import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QFrame,
    QMessageBox, QDialog, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
    QHeaderView, QScrollArea, QGridLayout, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..database.db_manager import LocalDatabaseManager
from ..services.pairing_service import DevicePairingService
from ..services.supabase_sync import SupabaseSyncWorker
from .theme import DARK_THEME_QSS, LIGHT_THEME_QSS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = LocalDatabaseManager()
        self.settings = self.db.get_shop_settings()
        self.current_theme = self.settings.get('theme_mode', 'Dark')
        
        self.setWindowTitle("E-Store POS & Management System")
        self.resize(1360, 860)
        self._apply_theme(self.current_theme)

        # Services
        self.pairing_service = DevicePairingService(self.db)
        self.cart = []
        self.active_category = "All"

        # Build UI
        self._setup_ui()
        self._load_category_pills()
        self._load_inventory_cards()
        self._load_analytics()

        # Start Async Sync Worker
        self.sync_worker = SupabaseSyncWorker(self.db)
        self.sync_worker.sync_status_signal.connect(self._update_sync_status)
        self.sync_worker.start()

    def _apply_theme(self, theme_name: str):
        self.current_theme = theme_name
        if theme_name == "Light":
            self.setStyleSheet(LIGHT_THEME_QSS)
        else:
            self.setStyleSheet(DARK_THEME_QSS)

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Header Bar
        header = QFrame()
        header.setObjectName("cardFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title_box = QVBoxLayout()
        self.shop_title_label = QLabel(self.settings.get('shop_name', 'E-Store'))
        self.shop_title_label.setObjectName("titleLabel")
        subtitle = QLabel("Electronics Accessories POS & Business Management System")
        subtitle.setObjectName("subtitleLabel")
        title_box.addWidget(self.shop_title_label)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Theme Switcher Button
        self.theme_btn = QPushButton(f"Theme: {self.current_theme}")
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.theme_btn)

        # Preferences Button
        settings_btn = QPushButton("Preferences")
        settings_btn.clicked.connect(self._open_settings_dialog)
        header_layout.addWidget(settings_btn)

        # Pair Mobile Button
        pair_btn = QPushButton("Mobile Pairing")
        pair_btn.setObjectName("accentButton")
        pair_btn.clicked.connect(self._open_pairing_dialog)
        header_layout.addWidget(pair_btn)

        main_layout.addWidget(header)

        # 2. Main Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: POS Card-Grid Billing Screen
        self.pos_tab = QWidget()
        self._setup_pos_tab()
        self.tabs.addTab(self.pos_tab, "POS Checkout")

        # Tab 2: Sales Return & Refund System
        self.return_tab = QWidget()
        self._setup_return_tab()
        self.tabs.addTab(self.return_tab, "Sales Returns & Refunds")

        # Tab 3: Hardware Inventory Catalog
        self.inventory_tab = QWidget()
        self._setup_inventory_tab()
        self.tabs.addTab(self.inventory_tab, "Hardware Products")

        # Tab 4: Dynamic Category Manager
        self.category_tab = QWidget()
        self._setup_category_tab()
        self.tabs.addTab(self.category_tab, "Category Manager")

        # Tab 5: Split Revenue Analytics
        self.analytics_tab = QWidget()
        self._setup_analytics_tab()
        self.tabs.addTab(self.analytics_tab, "Analytics & Reports")

        # Tab 6: Udhaar Ledger
        self.udhaar_tab = QWidget()
        self._setup_udhaar_tab()
        self.tabs.addTab(self.udhaar_tab, "Udhaar Ledger")

        main_layout.addWidget(self.tabs)
        self.statusBar().showMessage("System Active - Offline First Enabled")

    # --- TAB 1: POS BILLING SCREEN ---
    def _setup_pos_tab(self):
        layout = QHBoxLayout(self.pos_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # Left Container: Search + Dynamic Category Pills + Card Grid + USB Media Bar
        left_col = QFrame()
        left_col.setObjectName("cardFrame")
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        # Search Bar
        search_box = QHBoxLayout()
        self.pos_search_input = QLineEdit()
        self.pos_search_input.setPlaceholderText("Search product by name or barcode...")
        self.pos_search_input.textChanged.connect(lambda: self._load_inventory_cards())
        search_box.addWidget(self.pos_search_input)
        left_layout.addLayout(search_box)

        # Dynamic Category Pills Layout
        self.category_pills_layout = QHBoxLayout()
        self.category_button_group = QButtonGroup(self)
        left_layout.addLayout(self.category_pills_layout)

        # Product Cards Scroll Area
        self.cards_scroll_area = QScrollArea()
        self.cards_scroll_area.setWidgetResizable(True)
        self.cards_scroll_area.setStyleSheet("border: none; background: transparent;")

        self.cards_container = QWidget()
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setSpacing(12)
        self.cards_scroll_area.setWidget(self.cards_container)

        left_layout.addWidget(self.cards_scroll_area, stretch=3)

        # USB Media Copying Service Bar (Dynamic Custom Price Override)
        media_frame = QFrame()
        media_frame.setObjectName("cardFrame")
        media_layout = QHBoxLayout(media_frame)
        media_layout.setContentsMargins(12, 10, 12, 10)

        media_title = QLabel("USB Movie/Song Download Service:")
        media_title.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.media_type_combo = QComboBox()
        self.media_type_combo.addItems(["HD Movie Copy", "Songs MP3 Batch", "Software Download", "Custom USB Transfer"])

        self.media_qty_spin = QSpinBox()
        self.media_qty_spin.setRange(1, 1000)
        self.media_qty_spin.setValue(1)

        self.media_price_spin = QDoubleSpinBox()
        self.media_price_spin.setRange(0.0, 50000.0)
        self.media_price_spin.setValue(150.0)

        add_media_btn = QPushButton("Add Media Service")
        add_media_btn.setObjectName("accentButton")
        add_media_btn.clicked.connect(self._add_media_service_to_cart)

        media_layout.addWidget(media_title)
        media_layout.addWidget(self.media_type_combo, stretch=2)
        media_layout.addWidget(QLabel("Qty:"))
        media_layout.addWidget(self.media_qty_spin)
        media_layout.addWidget(QLabel("Custom Price:"))
        media_layout.addWidget(self.media_price_spin)
        media_layout.addWidget(add_media_btn)

        left_layout.addWidget(media_frame)

        layout.addWidget(left_col, stretch=3)

        # Right Column: Current Sales Invoice Cart Panel
        right_col = QFrame()
        right_col.setObjectName("cardFrame")
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(12)

        cart_title = QLabel("Current Sales Invoice")
        cart_title.setObjectName("titleLabel")
        right_layout.addWidget(cart_title)

        # Invoice Cart Table with Cancel / Remove Action Button
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(["Item Name", "Type", "Qty", "Price", "Total", "Action"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.verticalHeader().setDefaultSectionSize(38)
        right_layout.addWidget(self.cart_table)

        summary_frame = QFrame()
        summary_layout = QFormLayout(summary_frame)

        self.subtotal_label = QLabel("PKR 0.00")
        self.subtotal_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.discount_input = QLineEdit("0.00")
        self.discount_input.textChanged.connect(self._recalculate_cart)

        summary_layout.addRow("Subtotal:", self.subtotal_label)
        summary_layout.addRow("Discount:", self.discount_input)

        right_layout.addWidget(summary_frame)

        self.checkout_btn = QPushButton("Proceed to Payment [PKR 0.00]")
        self.checkout_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.checkout_btn.setObjectName("accentButton")
        self.checkout_btn.setStyleSheet("padding: 14px; font-weight: bold; border-radius: 6px;")
        self.checkout_btn.clicked.connect(self._complete_sale)
        right_layout.addWidget(self.checkout_btn)

        layout.addWidget(right_col, stretch=2)

    # --- CATEGORY PILLS MANAGER ---
    def _load_category_pills(self):
        # Clear existing layout
        for i in reversed(range(self.category_pills_layout.count())):
            widget = self.category_pills_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        categories = [c['name'] for c in self.db.get_categories()]
        all_categories = ["All"] + categories

        for idx, cat in enumerate(all_categories):
            btn = QPushButton(cat)
            btn.setObjectName("categoryTab")
            btn.setCheckable(True)
            if cat == self.active_category:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, c=cat: self._select_category_filter(c))
            self.category_button_group.addButton(btn)
            self.category_pills_layout.addWidget(btn)

    def _select_category_filter(self, category: str):
        self.active_category = category
        self._load_inventory_cards()

    # --- CARD GRID GENERATOR ---
    def _load_inventory_cards(self):
        for i in reversed(range(self.cards_grid.count())):
            widget = self.cards_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        query = self.pos_search_input.text()
        products = self.db.search_products(query, self.active_category)
        curr = self.settings.get('currency', 'PKR')

        if not products:
            no_products_lbl = QLabel("No products found in this category.\nAdd new products from the 'Hardware Products' tab.")
            no_products_lbl.setAlignment(Qt.AlignCenter)
            no_products_lbl.setStyleSheet("color: #94A3B8; font-size: 14px; padding: 40px;")
            self.cards_grid.addWidget(no_products_lbl, 0, 0)
            return

        columns = 3
        for idx, p in enumerate(products):
            row = idx // columns
            col = idx % columns

            card = QFrame()
            card.setObjectName("productCard")
            card_layout = QVBoxLayout(card)

            img_box = QLabel()
            img_box.setAlignment(Qt.AlignCenter)
            img_box.setFixedHeight(80)
            img_box.setStyleSheet("background-color: #0F172A; border-radius: 6px; color: #38BDF8; font-weight: bold;")
            img_box.setText(f"[ {p['category_name']} ]")
            card_layout.addWidget(img_box)

            title_lbl = QLabel(p['name'])
            title_lbl.setObjectName("productTitle")
            title_lbl.setWordWrap(True)

            price_lbl = QLabel(f"{curr} {p['selling_price']:.2f}")
            price_lbl.setObjectName("productPrice")

            stock_lbl = QLabel(f"Stock: {p['stock_quantity']}")
            stock_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")

            card_layout.addWidget(title_lbl)
            card_layout.addWidget(price_lbl)
            card_layout.addWidget(stock_lbl)

            add_btn = QPushButton("Add to Invoice")
            add_btn.setObjectName("accentButton")
            add_btn.clicked.connect(lambda _, item=p: self._add_hardware_to_cart(item))
            card_layout.addWidget(add_btn)

            self.cards_grid.addWidget(card, row, col)

    # --- TAB 2: SALES RETURNS & REFUNDS ---
    def _setup_return_tab(self):
        layout = QVBoxLayout(self.return_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Sales Return & Item Refund Processing")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Search Bar for Invoice Receipt
        search_frame = QFrame()
        search_frame.setObjectName("cardFrame")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 12, 14, 12)

        self.return_receipt_input = QLineEdit()
        self.return_receipt_input.setPlaceholderText("Enter Invoice Receipt Number (e.g. INV-20260913...)")
        
        search_btn = QPushButton("Search Invoice")
        search_btn.clicked.connect(self._search_invoice_for_return)

        search_layout.addWidget(QLabel("Receipt Number:"))
        search_layout.addWidget(self.return_receipt_input, stretch=2)
        search_layout.addWidget(search_btn)

        layout.addWidget(search_frame)

        # Invoice Details & Returnable Items Table
        self.return_info_label = QLabel("Enter an invoice number above to inspect items for return.")
        self.return_info_label.setStyleSheet("color: #94A3B8; font-size: 13px;")
        layout.addWidget(self.return_info_label)

        self.return_items_table = QTableWidget()
        self.return_items_table.setColumnCount(6)
        self.return_items_table.setHorizontalHeaderLabels(["Item Name", "Type", "Purchased Qty", "Unit Price", "Total Price", "Action"])
        self.return_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.return_items_table.verticalHeader().setDefaultSectionSize(38)
        layout.addWidget(self.return_items_table)

    def _search_invoice_for_return(self):
        receipt = self.return_receipt_input.text().strip()
        if not receipt:
            QMessageBox.warning(self, "Input Error", "Please enter a valid Invoice Receipt Number!")
            return

        sale = self.db.get_sale_by_receipt(receipt)
        if not sale:
            QMessageBox.warning(self, "Not Found", f"Invoice #{receipt} not found in sales history.")
            return

        curr = self.settings.get('currency', 'PKR')
        self.return_info_label.setText(
            f"Invoice #{sale['receipt_number']} | Date: {sale['created_at'][:16]} | Total: {curr} {sale['total_amount']:.2f} | Status: {sale['status']}"
        )

        items = sale['items']
        self.return_items_table.setRowCount(len(items))

        for row, item in enumerate(items):
            self.return_items_table.setItem(row, 0, QTableWidgetItem(item['product_name']))
            self.return_items_table.setItem(row, 1, QTableWidgetItem(item['item_type']))
            self.return_items_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            self.return_items_table.setItem(row, 3, QTableWidgetItem(f"{curr} {item['unit_price']:.2f}"))
            self.return_items_table.setItem(row, 4, QTableWidgetItem(f"{curr} {item['total_price']:.2f}"))

            return_btn = QPushButton("Process Return")
            return_btn.setObjectName("dangerButton")
            return_btn.clicked.connect(lambda _, s_id=sale['id'], i_item=item: self._process_item_return(s_id, i_item))
            self.return_items_table.setCellWidget(row, 5, return_btn)

    def _process_item_return(self, sale_id: str, item: dict):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Return Item: {item['product_name']}")
        form = QFormLayout(dlg)

        qty_spin = QSpinBox()
        qty_spin.setRange(1, item['quantity'])
        qty_spin.setValue(1)

        reason_input = QLineEdit("Customer Return / Defective")

        form.addRow("Return Quantity:", qty_spin)
        form.addRow("Return Reason:", reason_input)

        confirm_btn = QPushButton("Confirm Refund & Restore Stock")
        confirm_btn.setObjectName("dangerButton")
        form.addRow(confirm_btn)

        def confirm():
            res = self.db.process_sales_return(sale_id, item['id'], qty_spin.value(), reason_input.text())
            curr = self.settings.get('currency', 'PKR')
            QMessageBox.information(
                dlg, "Refund Completed",
                f"Successfully refunded {res['returned_qty']} x '{res['product_name']}'!\n"
                f"Refund Amount: {curr} {res['refund_amount']:.2f}\n"
                "Stock has been restored to inventory."
            )
            dlg.accept()
            self._search_invoice_for_return()
            self._load_inventory_cards()
            self._load_inventory_table()
            self._load_analytics()

        confirm_btn.clicked.connect(confirm)
        dlg.exec()

    # --- TAB 3: HARDWARE INVENTORY ---
    def _setup_inventory_tab(self):
        layout = QVBoxLayout(self.inventory_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_actions = QHBoxLayout()
        add_product_btn = QPushButton("Add New Product")
        add_product_btn.setObjectName("accentButton")
        add_product_btn.clicked.connect(self._open_add_product_dialog)
        top_actions.addWidget(add_product_btn)
        top_actions.addStretch()

        layout.addLayout(top_actions)

        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(8)
        self.inv_table.setHorizontalHeaderLabels(["ID", "Item Name", "Category", "Cost Price", "Selling Price", "Stock", "Threshold", "Action"])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inv_table.verticalHeader().setDefaultSectionSize(38)
        layout.addWidget(self.inv_table)
        self._load_inventory_table()

    def _load_inventory_table(self):
        products = self.db.get_all_products()
        self.inv_table.setRowCount(len(products))
        curr = self.settings.get('currency', 'PKR')

        for row, p in enumerate(products):
            self.inv_table.setItem(row, 0, QTableWidgetItem(p['id'][:8]))
            self.inv_table.setItem(row, 1, QTableWidgetItem(p['name']))
            self.inv_table.setItem(row, 2, QTableWidgetItem(p['category_name']))
            self.inv_table.setItem(row, 3, QTableWidgetItem(f"{curr} {p['cost_price']:.2f}"))
            self.inv_table.setItem(row, 4, QTableWidgetItem(f"{curr} {p['selling_price']:.2f}"))
            self.inv_table.setItem(row, 5, QTableWidgetItem(str(p['stock_quantity'])))
            self.inv_table.setItem(row, 6, QTableWidgetItem(str(p['low_stock_threshold'])))

            del_btn = QPushButton("Delete")
            del_btn.setObjectName("dangerButton")
            del_btn.clicked.connect(lambda _, p_id=p['id']: self._delete_product(p_id))
            self.inv_table.setCellWidget(row, 7, del_btn)

    def _delete_product(self, product_id: str):
        if QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this product?") == QMessageBox.Yes:
            self.db.delete_product(product_id)
            self._load_inventory_table()
            self._load_inventory_cards()

    # --- TAB 4: DYNAMIC CATEGORY MANAGER ---
    def _setup_category_tab(self):
        layout = QVBoxLayout(self.category_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Custom Categories Manager")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        add_frame = QFrame()
        add_frame.setObjectName("cardFrame")
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(14, 12, 14, 12)

        self.cat_name_input = QLineEdit()
        self.cat_name_input.setPlaceholderText("Enter category name (e.g. Fast Chargers, Cables, Earbuds)...")

        add_cat_btn = QPushButton("Add Category")
        add_cat_btn.setObjectName("accentButton")
        add_cat_btn.clicked.connect(self._add_category)

        add_layout.addWidget(QLabel("Category Name:"))
        add_layout.addWidget(self.cat_name_input, stretch=2)
        add_layout.addWidget(add_cat_btn)

        layout.addWidget(add_frame)

        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(3)
        self.cat_table.setHorizontalHeaderLabels(["ID", "Category Name", "Action"])
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cat_table.verticalHeader().setDefaultSectionSize(38)
        layout.addWidget(self.cat_table)

        self._load_category_table()

    def _load_category_table(self):
        categories = self.db.get_categories()
        self.cat_table.setRowCount(len(categories))
        for row, c in enumerate(categories):
            self.cat_table.setItem(row, 0, QTableWidgetItem(c['id'][:8]))
            self.cat_table.setItem(row, 1, QTableWidgetItem(c['name']))

            del_btn = QPushButton("Delete")
            del_btn.setObjectName("dangerButton")
            del_btn.clicked.connect(lambda _, c_id=c['id']: self._delete_category(c_id))
            self.cat_table.setCellWidget(row, 2, del_btn)

    def _add_category(self):
        name = self.cat_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Category Name cannot be empty!")
            return
        try:
            self.db.add_category(name)
            self.cat_name_input.clear()
            self._load_category_table()
            self._load_category_pills()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Category already exists or invalid: {str(e)}")

    def _delete_category(self, cat_id: str):
        if QMessageBox.question(self, "Confirm Delete", "Delete this category?") == QMessageBox.Yes:
            self.db.delete_category(cat_id)
            self._load_category_table()
            self._load_category_pills()

    # --- TAB 5: REVENUE ANALYTICS ---
    def _setup_analytics_tab(self):
        layout = QVBoxLayout(self.analytics_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("E-Store Revenue & Profit Analytics")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        cards_layout = QHBoxLayout()

        self.card_hardware_rev = QLabel("Hardware Sales: PKR 0.00")
        self.card_hardware_rev.setStyleSheet("font-size: 16px; font-weight: bold; padding: 18px; background: #0284C7; color: white; border-radius: 8px;")
        
        self.card_media_rev = QLabel("USB Media Copying: PKR 0.00")
        self.card_media_rev.setStyleSheet("font-size: 16px; font-weight: bold; padding: 18px; background: #10B981; color: white; border-radius: 8px;")

        self.card_net_profit = QLabel("Net Overall Profit: PKR 0.00")
        self.card_net_profit.setStyleSheet("font-size: 16px; font-weight: bold; padding: 18px; background: #7C3AED; color: white; border-radius: 8px;")

        cards_layout.addWidget(self.card_hardware_rev)
        cards_layout.addWidget(self.card_media_rev)
        cards_layout.addWidget(self.card_net_profit)

        layout.addLayout(cards_layout)

    # --- TAB 6: UDHAAR LEDGER ---
    def _setup_udhaar_tab(self):
        layout = QVBoxLayout(self.udhaar_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        info = QLabel("Customer & Supplier Udhaar Balance Management Ledger")
        info.setObjectName("titleLabel")
        layout.addWidget(info)

        self.udhaar_table = QTableWidget()
        self.udhaar_table.setColumnCount(5)
        self.udhaar_table.setHorizontalHeaderLabels(["Party Name", "Type", "Amount", "Transaction", "Notes"])
        self.udhaar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.udhaar_table.verticalHeader().setDefaultSectionSize(38)
        layout.addWidget(self.udhaar_table)

    # --- CART OPERATIONS & CANCELLATION ---
    def _add_hardware_to_cart(self, product):
        for item in self.cart:
            if item['id'] == product['id'] and item['item_type'] == 'Hardware':
                item['quantity'] += 1
                self._update_cart_table()
                return

        self.cart.append({
            'id': product['id'],
            'name': product['name'],
            'item_type': 'Hardware',
            'selling_price': product['selling_price'],
            'cost_price': product['cost_price'],
            'quantity': 1
        })
        self._update_cart_table()

    def _add_media_service_to_cart(self):
        service_name = self.media_type_combo.currentText()
        qty = self.media_qty_spin.value()
        custom_price = self.media_price_spin.value()

        self.cart.append({
            'id': None,
            'name': f"{service_name} ({qty} files/items)",
            'item_type': 'MediaService',
            'selling_price': custom_price,
            'cost_price': 0.0,
            'quantity': 1
        })
        self._update_cart_table()

    def _remove_item_from_cart(self, index: int):
        if 0 <= index < len(self.cart):
            self.cart.pop(index)
            self._update_cart_table()

    def _update_cart_table(self):
        self.cart_table.setRowCount(len(self.cart))
        subtotal = 0.0
        for row, item in enumerate(self.cart):
            total = item['quantity'] * item['selling_price']
            subtotal += total
            self.cart_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(item['item_type']))
            self.cart_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"{item['selling_price']:.2f}"))
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"{total:.2f}"))

            cancel_btn = QPushButton("Cancel")
            cancel_btn.setObjectName("dangerButton")
            cancel_btn.clicked.connect(lambda _, idx=row: self._remove_item_from_cart(idx))
            self.cart_table.setCellWidget(row, 5, cancel_btn)

        self._recalculate_cart()

    def _recalculate_cart(self):
        subtotal = sum(i['quantity'] * i['selling_price'] for i in self.cart)
        try:
            discount = float(self.discount_input.text())
        except ValueError:
            discount = 0.0
        
        final_total = max(0.0, subtotal - discount)
        curr = self.settings.get('currency', 'PKR')
        self.subtotal_label.setText(f"{curr} {final_total:.2f}")
        self.checkout_btn.setText(f"Proceed to Payment [{curr} {final_total:.2f}]")

    def _complete_sale(self):
        if not self.cart:
            QMessageBox.warning(self, "Empty Cart", "Please add items or media services to cart before checkout!")
            return

        try:
            discount = float(self.discount_input.text())
        except ValueError:
            discount = 0.0

        res = self.db.process_pos_sale(self.cart, payment_method="Cash", discount=discount)
        curr = self.settings.get('currency', 'PKR')
        
        QMessageBox.information(self, "Sale Completed", 
                                f"Invoice #{res['receipt_number']} generated!\n"
                                f"Total Amount: {curr} {res['total_amount']:.2f}\n"
                                f"Hardware Revenue: {curr} {res['hardware_revenue']:.2f}\n"
                                f"USB Media Revenue: {curr} {res['media_service_revenue']:.2f}\n\n"
                                "Mobile Push Alert dispatched to shop owner phone.")
        
        self.cart.clear()
        self.discount_input.setText("0.00")
        self._update_cart_table()
        self._load_inventory_cards()
        self._load_inventory_table()
        self._load_analytics()

    def _load_analytics(self):
        summary = self.db.get_split_revenue_summary()
        curr = self.settings.get('currency', 'PKR')
        self.card_hardware_rev.setText(f"Hardware Sales: {curr} {summary['total_hardware']:.2f}")
        self.card_media_rev.setText(f"USB Media Copying: {curr} {summary['total_media']:.2f}")
        self.card_net_profit.setText(f"Net Overall Profit: {curr} {summary['net_profit']:.2f}")

    # --- THEME & SETTINGS ---
    def _toggle_theme(self):
        new_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self._apply_theme(new_theme)
        self.theme_btn.setText(f"Theme: {new_theme}")
        self.db.save_shop_settings({'theme_mode': new_theme})

    def _open_settings_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("E-Store Preferences")
        form = QFormLayout(dlg)

        name_in = QLineEdit(self.settings.get('shop_name', ''))
        phone_in = QLineEdit(self.settings.get('phone', ''))
        addr_in = QLineEdit(self.settings.get('address', ''))
        curr_in = QLineEdit(self.settings.get('currency', 'PKR'))
        footer_in = QLineEdit(self.settings.get('receipt_footer', ''))

        form.addRow("Shop Name:", name_in)
        form.addRow("Phone:", phone_in)
        form.addRow("Address:", addr_in)
        form.addRow("Currency:", curr_in)
        form.addRow("Receipt Footer Note:", footer_in)

        save_btn = QPushButton("Save Preferences")
        save_btn.setObjectName("accentButton")
        form.addRow(save_btn)

        def save():
            new_settings = {
                "shop_name": name_in.text(),
                "phone": phone_in.text(),
                "address": addr_in.text(),
                "currency": curr_in.text(),
                "receipt_footer": footer_in.text(),
                "theme_mode": self.current_theme
            }
            self.db.save_shop_settings(new_settings)
            self.settings = new_settings
            self.shop_title_label.setText(name_in.text())
            self._load_inventory_cards()
            self._load_analytics()
            dlg.accept()

        save_btn.clicked.connect(save)
        dlg.exec()

    def _open_pairing_dialog(self):
        code = self.pairing_service.generate_pair_code()
        dlg = QDialog(self)
        dlg.setWindowTitle("Mobile Device Dynamic Pairing")
        layout = QVBoxLayout(dlg)

        info = QLabel("Enter this 6-Digit Pairing Code in your Flutter Mobile App:")
        code_lbl = QLabel(code)
        code_lbl.setFont(QFont("Consolas", 32, QFont.Bold))
        code_lbl.setAlignment(Qt.AlignCenter)
        code_lbl.setStyleSheet("color: #10B981; background: #0F172A; padding: 15px; border-radius: 6px;")

        layout.addWidget(info)
        layout.addWidget(code_lbl)
        dlg.exec()

    def _open_add_product_dialog(self):
        categories = [c['name'] for c in self.db.get_categories()]
        if not categories:
            QMessageBox.warning(self, "No Categories", "Please add at least one category in the 'Category Manager' tab first!")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Add New Product")
        form = QFormLayout(dlg)

        name_in = QLineEdit()
        cat_in = QComboBox()
        cat_in.addItems(categories)
        barcode_in = QLineEdit()
        cost_in = QDoubleSpinBox()
        cost_in.setMaximum(100000)
        price_in = QDoubleSpinBox()
        price_in.setMaximum(100000)
        qty_in = QSpinBox()
        qty_in.setMaximum(10000)

        form.addRow("Product Name:", name_in)
        form.addRow("Category:", cat_in)
        form.addRow("Barcode:", barcode_in)
        form.addRow("Cost Price:", cost_in)
        form.addRow("Selling Price:", price_in)
        form.addRow("Stock Quantity:", qty_in)

        save_btn = QPushButton("Save Product")
        save_btn.setObjectName("accentButton")
        form.addRow(save_btn)

        def save():
            if not name_in.text():
                QMessageBox.warning(dlg, "Error", "Product Name is required!")
                return
            self.db.add_or_update_product({
                "name": name_in.text(),
                "category_name": cat_in.currentText(),
                "barcode": barcode_in.text(),
                "cost_price": cost_in.value(),
                "selling_price": price_in.value(),
                "stock_quantity": qty_in.value()
            })
            dlg.accept()
            self._load_inventory_cards()
            self._load_inventory_table()

        save_btn.clicked.connect(save)
        dlg.exec()

    def _update_sync_status(self, text: str, pending_count: int):
        self.statusBar().showMessage(f"Cloud Sync: {text} | Offline Queue: {pending_count}")

    def closeEvent(self, event):
        self.sync_worker.stop()
        event.accept()
