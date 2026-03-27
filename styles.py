MAIN_STYLE = """
/* The Architectural Ledger Design System */

QWidget {
    font-family: 'Segoe UI', 'Inter', 'Helvetica', sans-serif;
    font-size: 13px;
    color: #111c2d;
}

QMainWindow, #ContentArea {
    background-color: #f0f3ff;
}

/* Velvet Depth Login Background */
#LoginWindow {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #091426, stop:1 #1e293b);
}

/* Sidebar Styling */
#Sidebar {
    background-color: #091426;
    border-right: 1px solid rgba(30, 41, 59, 0.5);
}
#Sidebar QLabel {
    color: #ffffff;
}
#Sidebar QPushButton {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    padding: 12px 24px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}
#Sidebar QPushButton:hover {
    background-color: rgba(30, 41, 59, 0.5);
    color: #ffffff;
}
#Sidebar QPushButton:checked {
    background-color: #1e293b;
    color: #4edea3;
    font-weight: bold;
    border-left: 4px solid #0058be;
}

/* Typography & Titles */
*[class="TitleLabel"] {
    font-family: 'Manrope', 'Segoe UI', sans-serif;
    font-size: 32px;
    font-weight: 800;
    color: #091426;
    margin-bottom: 2px;
}
*[class="SubtitleLabel"] {
    font-size: 14px;
    color: #45474c;
    margin-bottom: 20px;
}
*[class="KPIValue"] {
    font-size: 38px;
    font-weight: 900;
    color: #091426;
}
*[class="KPILabel"] {
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #8590a6;
}

/* White Cards */
*[class="CardWidget"] {
    background-color: #ffffff;
    border-radius: 12px;
}
*[class="KPICard"] {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid rgba(197, 198, 205, 0.3);
}

/* Specific Top Nav */
#TopNav {
    background-color: rgba(255, 255, 255, 0.9);
    border-bottom: 1px solid rgba(197, 198, 205, 0.2);
}

/* No-Line Rule Inputs */
QLineEdit, QComboBox, QDateEdit {
    background-color: #dee8ff;
    color: #111c2d;
    border: none;
    border-radius: 8px;
    padding: 12px 14px;
    min-height: 24px;
    font-size: 14px;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 2px solid rgba(0, 88, 190, 0.4);
}

QComboBox::drop-down {
    border: none;
    background: transparent;
    padding-right: 15px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #c5c6cd;
    selection-background-color: #0058be;
    selection-color: #ffffff;
}

/* Action Buttons */
QPushButton {
    font-size: 14px;
    font-weight: bold;
    border-radius: 12px;
    padding: 12px 20px;
}
*[class="PrimaryButton"] {
    background-color: #0058be;
    color: white;
    border: none;
}
*[class="PrimaryButton"]:hover {
    background-color: #2170e4;
}

*[class="GhostButton"] {
    background-color: #ffffff;
    color: #0058be;
    border: 1px solid rgba(197, 198, 205, 0.3);
}
*[class="GhostButton"]:hover {
    background-color: #f0f3ff;
}

*[class="SuccessButton"] {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #005236, stop:1 #4edea3);
    color: #ffffff;
    border: none;
}
*[class="SuccessButton"]:hover {
    background: #4edea3;
}

*[class="DangerButton"] {
    background-color: #f9f9ff;
    border: 1px solid rgba(186, 26, 26, 0.3); 
    color: #ba1a1a;
}
.DangerButton:hover {
    background-color: #ffdad6;
    border: 1px solid #ba1a1a;
}

*[class="AttendanceActionBtn"] {
    background-color: #ffffff;
    border: 2px solid transparent;
    border-radius: 8px;
    color: #45474c;
    font-size: 11px;
    padding: 8px 12px;
}
*[class="AttendanceActionBtn"]:hover {
    background-color: #dee8ff;
}
*[class="BadgeDesignation"] {
    background-color: #dee8ff;
    color: #0058be;
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
}

/* Tables & ScrollAreas */
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
QTableWidget {
    background-color: #ffffff;
    border: none;
    gridline-color: transparent;
    border-radius: 12px;
}
QHeaderView::section {
    background-color: rgba(240, 243, 255, 0.5);
    color: #45474c;
    padding: 14px 18px;
    border: none;
    border-bottom: 1px solid rgba(197, 198, 205, 0.1);
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
QTableWidget::item {
    border-bottom: 1px solid rgba(197, 198, 205, 0.15);
    padding: 12px 18px;
}
QTableWidget::item:selected {
    background-color: rgba(240, 243, 255, 0.8);
    color: #111c2d;
}
QScrollBar:vertical {
    border: none;
    background: #f0f3ff;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #c5c6cd;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #8590a6;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Radios */
QRadioButton {
    color: #111c2d;
    font-weight: 500;
}

/* Dialogs */
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #111c2d;
    font-size: 14px;
}
QMessageBox QPushButton {
    background-color: #0058be;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background-color: #2170e4;
}
"""
