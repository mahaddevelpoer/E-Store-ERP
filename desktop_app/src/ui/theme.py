"""
E-Store Theme Engine: Strict High-Contrast & Spacious Layout Architecture
Guarantees 100% readable text in both Light and Dark themes with generous padding.
"""

DARK_THEME_QSS = """
QMainWindow {
    background-color: #0F172A;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #F8FAFC;
}

QDialog {
    background-color: #1E293B;
    color: #F8FAFC;
}

QFrame#cardFrame {
    background-color: #1E293B;
    border-radius: 8px;
    border: 1px solid #334155;
}

QFrame#productCard {
    background-color: #1E293B;
    border-radius: 8px;
    border: 1px solid #334155;
    padding: 10px;
}

QFrame#productCard:hover {
    border: 1px solid #38BDF8;
}

QLabel {
    color: #F8FAFC;
}

QLabel#productTitle {
    font-size: 13px;
    font-weight: bold;
    color: #F8FAFC;
}

QLabel#productPrice {
    font-size: 14px;
    font-weight: bold;
    color: #38BDF8;
}

QLabel#titleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #38BDF8;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #94A3B8;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #FFFFFF;
    min-height: 24px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #38BDF8;
}

QComboBox QAbstractItemView {
    background-color: #0F172A;
    color: #FFFFFF;
    selection-background-color: #0284C7;
    selection-color: #FFFFFF;
}

QPushButton {
    background-color: #0284C7;
    color: #FFFFFF;
    font-weight: 600;
    border-radius: 6px;
    padding: 9px 18px;
    border: none;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #0369A1;
}

QPushButton#accentButton {
    background-color: #10B981;
    color: #FFFFFF;
}

QPushButton#accentButton:hover {
    background-color: #059669;
}

QPushButton#dangerButton {
    background-color: #EF4444;
    color: #FFFFFF;
}

QPushButton#dangerButton:hover {
    background-color: #DC2626;
}

QPushButton#categoryTab {
    background-color: #0F172A;
    color: #94A3B8;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: bold;
}

QPushButton#categoryTab:checked, QPushButton#categoryTab:hover {
    background-color: #0284C7;
    color: #FFFFFF;
}

QTableWidget {
    background-color: #1E293B;
    gridline-color: #334155;
    border-radius: 6px;
    border: 1px solid #334155;
    color: #FFFFFF;
    selection-background-color: #0284C7;
    selection-color: #FFFFFF;
}

QTableWidget::item {
    padding: 6px;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #0F172A;
    color: #38BDF8;
    padding: 10px;
    font-weight: bold;
    border: none;
}

QStatusBar {
    background-color: #0F172A;
    color: #94A3B8;
}

QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #0F172A;
}

QTabBar::tab {
    background-color: #1E293B;
    color: #94A3B8;
    padding: 9px 20px;
    font-weight: bold;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0284C7;
    color: #FFFFFF;
}
"""

LIGHT_THEME_QSS = """
QMainWindow {
    background-color: #F8FAFC;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    color: #0F172A;
}

QDialog {
    background-color: #FFFFFF;
    color: #0F172A;
}

QFrame#cardFrame {
    background-color: #FFFFFF;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
}

QFrame#productCard {
    background-color: #FFFFFF;
    border-radius: 8px;
    border: 1px solid #CBD5E1;
    padding: 10px;
}

QFrame#productCard:hover {
    border: 1px solid #0284C7;
}

QLabel {
    color: #0F172A;
}

QLabel#productTitle {
    font-size: 13px;
    font-weight: bold;
    color: #0F172A;
}

QLabel#productPrice {
    font-size: 14px;
    font-weight: bold;
    color: #0284C7;
}

QLabel#titleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #0284C7;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #64748B;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #F1F5F9;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 12px;
    color: #0F172A;
    min-height: 24px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #0284C7;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #0F172A;
    selection-background-color: #0284C7;
    selection-color: #FFFFFF;
}

QPushButton {
    background-color: #0284C7;
    color: #FFFFFF;
    font-weight: 600;
    border-radius: 6px;
    padding: 9px 18px;
    border: none;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #0369A1;
}

QPushButton#accentButton {
    background-color: #10B981;
    color: #FFFFFF;
}

QPushButton#accentButton:hover {
    background-color: #059669;
}

QPushButton#dangerButton {
    background-color: #EF4444;
    color: #FFFFFF;
}

QPushButton#dangerButton:hover {
    background-color: #DC2626;
}

QPushButton#categoryTab {
    background-color: #E2E8F0;
    color: #475569;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: bold;
}

QPushButton#categoryTab:checked, QPushButton#categoryTab:hover {
    background-color: #0284C7;
    color: #FFFFFF;
}

QTableWidget {
    background-color: #FFFFFF;
    gridline-color: #E2E8F0;
    border-radius: 6px;
    border: 1px solid #CBD5E1;
    color: #0F172A;
    selection-background-color: #0284C7;
    selection-color: #FFFFFF;
}

QTableWidget::item {
    padding: 6px;
    color: #0F172A;
}

QHeaderView::section {
    background-color: #F1F5F9;
    color: #0284C7;
    padding: 10px;
    font-weight: bold;
    border: none;
}

QStatusBar {
    background-color: #F1F5F9;
    color: #64748B;
}

QTabWidget::pane {
    border: 1px solid #E2E8F0;
    background-color: #F8FAFC;
}

QTabBar::tab {
    background-color: #E2E8F0;
    color: #475569;
    padding: 9px 20px;
    font-weight: bold;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0284C7;
    color: #FFFFFF;
}
"""
